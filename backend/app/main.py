from fastapi import FastAPI

app = FastAPI(title="Supply Parser API")

@app.get("/")
def hello():
    return "hello world"