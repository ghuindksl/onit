import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Product, Visit

app = FastAPI(title="ONIT ORM Lab")
NODE_NAME = os.getenv("NODE_NAME", "app-node")


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    calories: float = Field(ge=0)
    proteins: float = Field(ge=0)
    fats: float = Field(ge=0)
    carbs: float = Field(ge=0)


class ProductOut(ProductCreate):
    id: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ONIT ORM Products</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .row {{ margin-bottom: 12px; }}
    input {{ margin-right: 8px; padding: 6px; }}
    button {{ padding: 8px 12px; margin-right: 8px; cursor: pointer; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f4f4f4; }}
    .hint {{ color: #555; }}
  </style>
</head>
<body>
  <h2>Работа с PostgreSQL через ORM ({NODE_NAME})</h2>
  <p class="hint">Добавьте продукт питания, удалите запись по id и просматривайте данные таблицы ниже.</p>

  <div class="row">
    <input id="name" placeholder="Название (например, Гречка)" />
    <input id="calories" type="number" step="0.1" min="0" placeholder="Ккал" />
    <input id="proteins" type="number" step="0.1" min="0" placeholder="Белки" />
    <input id="fats" type="number" step="0.1" min="0" placeholder="Жиры" />
    <input id="carbs" type="number" step="0.1" min="0" placeholder="Углеводы" />
    <button onclick="addProduct()">Добавить запись</button>
  </div>

  <div class="row">
    <input id="deleteId" type="number" min="1" placeholder="ID для удаления" />
    <button onclick="deleteProduct()">Удалить запись</button>
    <button onclick="loadProducts()">Обновить таблицу</button>
  </div>

  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Название</th>
        <th>Ккал</th>
        <th>Белки</th>
        <th>Жиры</th>
        <th>Углеводы</th>
      </tr>
    </thead>
    <tbody id="productsBody"></tbody>
  </table>

  <script>
    async function loadProducts() {{
      const response = await fetch("/products");
      const data = await response.json();
      const tbody = document.getElementById("productsBody");
      tbody.innerHTML = "";

      for (const item of data) {{
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${{item.id}}</td>
          <td>${{item.name}}</td>
          <td>${{item.calories}}</td>
          <td>${{item.proteins}}</td>
          <td>${{item.fats}}</td>
          <td>${{item.carbs}}</td>
        `;
        tbody.appendChild(row);
      }}
    }}

    async function addProduct() {{
      const payload = {{
        name: document.getElementById("name").value.trim(),
        calories: Number(document.getElementById("calories").value),
        proteins: Number(document.getElementById("proteins").value),
        fats: Number(document.getElementById("fats").value),
        carbs: Number(document.getElementById("carbs").value),
      }};

      if (!payload.name) {{
        alert("Введите название продукта");
        return;
      }}

      const response = await fetch("/products", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload),
      }});

      if (!response.ok) {{
        alert("Не удалось добавить запись");
        return;
      }}

      await loadProducts();
    }}

    async function deleteProduct() {{
      const id = Number(document.getElementById("deleteId").value);
      if (!id) {{
        alert("Введите корректный ID");
        return;
      }}

      const response = await fetch(`/products/${{id}}`, {{ method: "DELETE" }});
      if (!response.ok) {{
        alert("Запись не найдена или не удалена");
        return;
      }}
      await loadProducts();
    }}

    loadProducts();
  </script>
</body>
</html>
"""


@app.post("/visits")
def create_visit(db: Session = Depends(get_db)) -> dict:
    visit = Visit()
    db.add(visit)
    db.commit()
    db.refresh(visit)
    total = db.query(Visit).count()
    return {"visit_id": visit.id, "total_visits": total}


@app.post("/products", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductOut:
    product = Product(
        name=payload.name,
        calories=payload.calories,
        proteins=payload.proteins,
        fats=payload.fats,
        carbs=payload.carbs,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductOut(
        id=product.id,
        name=product.name,
        calories=product.calories,
        proteins=product.proteins,
        fats=product.fats,
        carbs=product.carbs,
    )


@app.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)) -> list[ProductOut]:
    products = db.query(Product).order_by(Product.id.asc()).all()
    return [
        ProductOut(
            id=p.id,
            name=p.name,
            calories=p.calories,
            proteins=p.proteins,
            fats=p.fats,
            carbs=p.carbs,
        )
        for p in products
    ]


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"status": "deleted", "id": product_id}


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ok"}
