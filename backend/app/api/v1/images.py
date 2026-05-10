"""KineIA Image Proxy — fetches free anatomical images from Wikimedia Commons."""

import httpx
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/images", tags=["images"])

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

# Anatomical terms mapped to Wikimedia Commons category/image titles
ANATOMY_IMAGE_MAP = {
    "hombro": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Shoulder_joint_bf.svg/800px-Shoulder_joint_bf.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Pectoralis_major.png/400px-Pectoralis_major.png",
    ],
    "rodilla": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Knee_diagram_es.svg/800px-Knee_diagram_es.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Blausen_0597_KneeAnatomy_Side.png/800px-Blausen_0597_KneeAnatomy_Side.png",
    ],
    "columna": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Illu_vertebral_column-es.svg/400px-Illu_vertebral_column-es.svg.png",
    ],
    "lca": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Knee_diagram_es.svg/800px-Knee_diagram_es.svg.png",
    ],
    "cadera": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Hip_joint-es.svg/600px-Hip_joint-es.svg.png",
    ],
    "codo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Elbow_es.svg/800px-Elbow_es.svg.png",
    ],
    "muñeca": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Wrist_and_hand_deeper_palmar_es.svg/400px-Wrist_and_hand_deeper_palmar_es.svg.png",
    ],
    "tobillo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Ankle_es.svg/800px-Ankle_es.svg.png",
    ],
    "pie": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Blausen_0411_FootAnatomy.png/600px-Blausen_0411_FootAnatomy.png",
    ],
    "mano": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Wrist_and_hand_deeper_palmar_es.svg/400px-Wrist_and_hand_deeper_palmar_es.svg.png",
    ],
    "craneo": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Human_skull_side_simplified_%28bones%29-es.svg/400px-Human_skull_side_simplified_%28bones%29-es.svg.png",
    ],
    "torax": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Thoracic_landmarks_anterior_view-es.svg/400px-Thoracic_landmarks_anterior_view-es.svg.png",
    ],
    "pelvis": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Pelvis_diagram_es.svg/400px-Pelvis_diagram_es.svg.png",
    ],
    "musculos": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Muscles_anterior_labeled.png/400px-Muscles_anterior_labeled.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Muscles_posterior_labeled.png/400px-Muscles_posterior_labeled.png",
    ],
    "sistema nervioso": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Nervous_system_diagram-es.svg/400px-Nervous_system_diagram-es.svg.png",
    ],
    "corazon": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Heart_anterior_exterior_es.svg/600px-Heart_anterior_exterior_es.svg.png",
    ],
    "pulmones": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Lungs_diagram_detailed-es.svg/600px-Lungs_diagram_detailed-es.svg.png",
    ],
    "medula espinal": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Spinal_cord_diagram-es.svg/400px-Spinal_cord_diagram-es.svg.png",
    ],
}


@router.get("/search")
async def search_images(
    q: str = Query(..., description="Término anatómico a buscar"),
):
    """Search for free anatomical images by keyword."""
    query_lower = q.lower().strip()
    results = []

    # Direct matches
    for key, urls in ANATOMY_IMAGE_MAP.items():
        if key in query_lower or query_lower in key:
            for url in urls:
                results.append({
                    "url": url,
                    "label": key.capitalize(),
                    "source": "Wikimedia Commons",
                    "license": "CC BY-SA / Public Domain",
                })

    # If no direct match, search Wikimedia API
    if not results:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    WIKIMEDIA_API,
                    params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": f"{q} anatomy filetype:svg|png",
                        "gsrlimit": 5,
                        "gsrnamespace": 6,  # File namespace
                        "prop": "imageinfo",
                        "iiprop": "url",
                        "format": "json",
                    },
                )
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    image_info = page.get("imageinfo", [{}])[0]
                    url = image_info.get("url", "")
                    if url:
                        results.append({
                            "url": url,
                            "label": page.get("title", "Imagen"),
                            "source": "Wikimedia Commons",
                            "license": "Ver Wikimedia Commons",
                        })
        except Exception:
            pass

    if not results:
        return JSONResponse(
            status_code=404,
            content={
                "status": "not_found",
                "message": f"No se encontraron imágenes para '{q}'. Probá con: hombro, rodilla, columna, cadera, codo, tobillo, mano, craneo, torax, pelvis, musculos, corazon, pulmones, medula espinal, sistema nervioso.",
                "suggestions": list(ANATOMY_IMAGE_MAP.keys()),
            },
        )

    return {"status": "success", "data": results}


@router.get("/list")
async def list_available():
    """List all available anatomical image categories."""
    return {
        "status": "success",
        "data": {
            term: [{"url": urls[0], "count": len(urls)}]
            for term, urls in sorted(ANATOMY_IMAGE_MAP.items())
        },
    }
