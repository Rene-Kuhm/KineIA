from pathlib import Path
from app.core.ingestion.pipeline import ingest_directory

KB_PATH = Path("/app/knowledge_base")

if __name__ == "__main__":
    print(f"🔄 Ingesting knowledge base from {KB_PATH}")
    results = ingest_directory(str(KB_PATH), recursive=True)
    
    success = sum(1 for r in results if r.get("status") == "success")
    errors = sum(1 for r in results if r.get("status") == "error")
    
    print(f"\n✅ Ingest complete: {success} files, {errors} errors")
    
    for r in results:
        if r.get("status") == "error":
            print(f"  ❌ {r.get('file')}: {r.get('error')}")