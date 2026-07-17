import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import RateLimitMiddleware
from app.api.v1 import auth, chat, images, knowledge, search
from app.config import settings
from app.db.postgres import Base, engine
from app.db.qdrant import get_qdrant, init_qdrant_collection
from app.services.rag.hybrid_gate import HybridGate, build_hybrid_gate
from app.services.rag.retriever import Retriever

logger = logging.getLogger(__name__)


async def create_retriever(config=settings, client=None):
    client = client or get_qdrant()
    if config.retriever_read_mode == "dense":
        return Retriever(client=client, read_mode="dense")
    try:
        gate = await asyncio.wait_for(
            asyncio.to_thread(build_hybrid_gate, config, client),
            timeout=config.hybrid_readiness_timeout_seconds,
        )
    except Exception as error:
        gate = HybridGate(reason="startup_check_failed")
        with suppress(Exception):
            logger.warning("hybrid_readiness status=disabled reason=%s exception_class=%s",
                           gate.reason, type(error).__name__)
    else:
        log = logger.info if gate.allows_hybrid() else logger.warning
        with suppress(Exception):
            log("hybrid_readiness status=%s reason=%s",
                "enabled" if gate.allows_hybrid() else "disabled", gate.reason)
    return Retriever(client=client, read_mode="hybrid", gate=gate)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_qdrant_collection()
    app.state.retriever = await create_retriever()
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

app.add_middleware(RateLimitMiddleware)


app.include_router(chat.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")


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
