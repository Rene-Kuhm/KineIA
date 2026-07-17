# ruff: noqa: E501
from app.services.rag.citations import format_sources


def test_sources_have_stable_nullable_schema_without_path_fallbacks():
    document = {"metadata": {"title": "Guide", "original_source_name": "guide.md",
        "source_id": "doi:10.1000/guide", "source_version_id": "v1", "chunk_index": 2,
        "fragment_hash": "a" * 64, "section_heading": "Exercise", "section_path": ["Knee", "Exercise"],
        "url": "https://example.org/guide", "doi": "10.1000/guide", "isbn": "9781402894626",
        "publication_date": "2025-04-01", "review_date": "2026-07-16", "evidence_level": "guideline"},
        "score": 0.91, "retrieval_mode": "hybrid", "score_type": "rrf"}
    legacy = {"title": r"C:\private\legacy.md", "source": r"C:\private\legacy.md", "url": "file:///private/legacy.md",
              "doi": "10.1000/bad\nvalue", "publication_date": "2025-01-01\tcorrupt", "evidence_level": "bad\x00value"}
    source, old_source = format_sources([document, legacy])
    assert format_sources(None) == format_sources({}) == format_sources([None, "bad", {}]) == []
    assert format_sources(legacy) == [old_source]
    assert format_sources({"b": legacy, "a": document, "bad": 7}) == [source, old_source]
    assert source["source"] == source["original_source_name"] == "guide.md"
    assert source["section_path"] == ["Knee", "Exercise"] and source["page_start"] is source["page_end"] is None
    assert set(source) == set(old_source)
    assert old_source["source"] == old_source["original_source_name"] == old_source["title"] == "legacy.md"
    nullable = ("url", "doi", "isbn", "publication_date", "review_date", "evidence_level", "section_heading", "section_path", "page_start", "page_end")
    assert all(old_source[key] is None for key in nullable) and "private" not in repr(old_source)
