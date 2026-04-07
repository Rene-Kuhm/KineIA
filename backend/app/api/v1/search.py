from fastapi import APIRouter, Query

from app.services.rag.retriever import retriever

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_knowledge(
    q: str = Query(..., description="Query string"),
    area: str | None = Query(None, description="Filter by area"),
    evidence_level: str | None = Query(None, description="Filter by evidence level"),
    limit: int = Query(5, description="Number of results"),
):
    results = retriever.search(query=q, area=area, evidence_level=evidence_level, limit=limit)
    return {"status": "success", "data": results}


@router.get("/filters")
async def get_search_filters():
    return {
        "areas": [
            "anatomia",
            "fisiologia",
            "kinesiologia",
            "traumatologia",
            "neurologia",
            "respiratorio",
            "deportivo",
            "pediatria",
        ],
        "source_types": ["book", "protocol", "paper", "notes"],
        "evidence_levels": ["protocol", "book", "paper", "notes"],
    }
