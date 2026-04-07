from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.postgres import engine, Base
from app.db.qdrant import init_qdrant_collection
from app.api.v1 import chat, search, auth, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_qdrant_collection()
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="KineIA API",
    description="Expert AI Agent for Kinesiologists - RAG-powered knowledge base",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/api/v1/health")
async def api_health():
    return {
        "status": "healthy",
        "services": {
            "api": True,
            "database": True,
            "qdrant": True,
        },
    }
