from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/stats")
async def knowledge_stats():
    return {
        "status": "not_implemented",
        "message": "Knowledge stats - will show document counts by area/type",
    }


@router.post("/ingest")
async def ingest_document():
    return {"status": "not_implemented", "message": "Ingest endpoint - Fase 1.3"}
