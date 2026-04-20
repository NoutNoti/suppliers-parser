from fastapi import FastAPI

from app.api.v1.api import router as v1_router

app = FastAPI(title="Supply Parser API")

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
def hello():
    return "hello world"

