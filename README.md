# ONIT Labs 1-4

Проект покрывает требования из 4 лабораторных работ:

1. ORM-приложение (`FastAPI + SQLAlchemy + PostgreSQL`).
2. Контейнеризация (`multi-stage`, приложение отдельно от БД, `depends_on`, healthcheck, переменные через окружение).
3. CI/CD через `GitHub Actions` с функциональным тестом.
4. Балансировка Nginx (round-robin) между 3 нодами.

## Лаба 1: ORM

Основное приложение находится в `app/`:
- `app/database.py` - подключение к БД и ORM-сессии.
- `app/models.py` - ORM модели `Visit` и `Product`.
- `app/main.py` - API:
  - `GET /` - описание API для работы с PostgreSQL.
  - `POST /visits` - создает запись через ORM и возвращает общее число посещений.
  - `POST /products` - добавляет продукт питания в БД.
  - `GET /products` - возвращает список добавленных продуктов.
  - `GET /health` - проверка приложения и БД.

### Пример явного взаимодействия с PostgreSQL через ORM
Добавить продукт:
```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Buckwheat","calories":343,"proteins":13.3,"fats":3.4,"carbs":71.5}'
```

Получить все продукты:
```bash
curl http://localhost:8000/products
```

## Лаба 2: Docker

### Что выполнено
- `Dockerfile` с **multi-stage** сборкой.
- `docker-compose.yml`: сервисы `app` и `db` разделены.
- Параметры подключения передаются через переменные окружения (`.env`).
- Используется `depends_on` c условием `service_healthy` для БД.
- Для приложения настроен `healthcheck`.

### Запуск
1. Скопировать пример переменных:
   ```bash
   cp .env.example .env
   ```
2. Запустить:
   ```bash
   docker compose --env-file .env up -d --build
   ```
3. Проверить:
   - `http://localhost:8000/`
   - `http://localhost:8000/health`

Остановка:
```bash
docker compose down -v
```

## Лаба 3: GitHub Actions CI/CD

Workflow: `.github/workflows/ci.yml`

### Требования к секретам/переменным в GitHub
- `vars.DB_NAME`
- `secrets.DB_USER`
- `secrets.DB_PASSWORD`

### Что делает pipeline
1. Создает `.env` на основе GitHub Variables/Secrets.
2. Поднимает контейнеры через `docker compose`.
3. Ждет готовность `GET /health`.
4. Запускает функциональный тест `tests/functional_test.sh`.
5. Останавливает контейнеры.

## Лаба 4: Nginx round-robin

Отдельный стенд в `lab4/`:
- `lab4/node_app/` - простое веб-приложение, показывающее имя ноды.
- `lab4/nginx/nginx.conf` - upstream из 3 нод.
- `lab4/docker-compose.yml` - поднимает 3 ноды + Nginx.

### Запуск
```bash
cd lab4
docker compose up -d --build
```

Открыть `http://localhost:8080/` и обновлять страницу - будут меняться ответы:
- `Node 1`
- `Node 2`
- `Node 3`

Остановка:
```bash
docker compose down
```
