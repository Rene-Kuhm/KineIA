#!/usr/bin/env python3
"""Seed the knowledge base by ingesting all documents into Qdrant."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.ingestion.pipeline import ingest_directory


def main():
    knowledge_base = Path(__file__).parent.parent / "knowledge_base"

    if not knowledge_base.exists():
        print(f"❌ Knowledge base directory not found: {knowledge_base}")
        sys.exit(1)

    print("🧠 KineIA - Seeding Knowledge Base")
    print("=" * 50)

    directories = [
        ("universidades", "University curricula and programs"),
        ("libros", "Reference textbooks"),
        ("protocolos", "Clinical protocols"),
        ("guias-clinicas", "Clinical guidelines"),
        ("papers", "Research papers"),
        ("normativa", "Regulations and standards"),
    ]

    total_chunks = 0
    total_files = 0
    errors = 0

    for dir_name, description in directories:
        dir_path = knowledge_base / dir_name
        if not dir_path.exists():
            print(f"\n⏭️  Skipping {dir_name}/ (not found)")
            continue

        files = list(dir_path.glob("**/*.md")) + list(dir_path.glob("**/*.pdf"))
        if not files:
            print(f"\n⏭️  Skipping {dir_name}/ (empty)")
            continue

        print(f"\n📂 {dir_name}/ — {description}")
        print(f"   Found {len(files)} files")

        results = ingest_directory(str(dir_path))

        for r in results:
            if r["status"] == "success":
                total_chunks += r["chunks"]
                total_files += 1
            else:
                errors += 1

    print("\n" + "=" * 50)
    print(f"✅ Ingestion complete!")
    print(f"   Files processed: {total_files}")
    print(f"   Total chunks: {total_chunks}")
    print(f"   Errors: {errors}")


if __name__ == "__main__":
    main()
