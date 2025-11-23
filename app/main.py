from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.artifacts.models import init_db
from app.data.routes import generate as data_generate
from app.train.routes import train as train_routes
from app.evaluate.routes import evaluate as evaluate_routes
from app.prune.routes import prune as prune_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="Credit Risk MLOps API",
    version="1.0",
    lifespan=lifespan,
)


app.include_router(data_generate.router)
app.include_router(train_routes.router)
app.include_router(evaluate_routes.router)
app.include_router(prune_routes.router)


@app.get("/")
def root():
    return {"message": "Credit Risk MLOps API is live"}
