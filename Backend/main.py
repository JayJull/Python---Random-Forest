from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import get_db, close_connection
from model.lead import ensure_indexes
from routers.scrape import router as scrape_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    await ensure_indexes(db)
    yield
    await close_connection()


app = FastAPI(
    title="Google Maps Scraper API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape_router)


@app.get("/health")
async def health():
    return {"status": "ok"}