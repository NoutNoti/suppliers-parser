import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.product import router as v1_router
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Supply Parser API", lifespan=lifespan)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
def hello():
    return "hello world"
