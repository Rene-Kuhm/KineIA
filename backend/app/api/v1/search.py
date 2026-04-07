from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_knowledge():
    return {"status": "not_implemented", "message": "Search endpoint - Fase 2"}


@router.get("/filters")
async def get_search_filters():
    return {
        "areas": [
            "anatomia", "fisiologia", "kinesiologia", "traumatologia",
            "neurologia", "respiratorio", "deportivo", "pediatria",
        ],
        "source_types": ["book", "protocol", "paper", "notes"],
        "evidence_levels": ["protocol", "book", "paper", "notes"],
    }
