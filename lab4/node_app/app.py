import os

from flask import Flask

app = Flask(__name__)
NODE_NAME = os.getenv("NODE_NAME", "node-unknown")


@app.get("/")
def index():
    return f"<h1>{NODE_NAME}</h1>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
