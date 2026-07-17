# ruff: noqa: E501, I001
import math
import re
from app.core.ingestion import provenance as citation
_TEXT_FIELDS = ("source_id", "source_version", "source_version_id")
_SINGLE_KEYS = _TEXT_FIELDS + ("metadata", "title", "source", "original_source_name", "content_hash", "chunk_index", "fragment_hash", "section_heading", "section_path", "page_start", "page_end", "url", "doi", "isbn", "publication_date", "review_date", "evidence_level", "score", "retrieval_mode", "score_type")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
def _integer(value, minimum=0):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= minimum else None
def _hash(value):
    value = citation.safe_citation_text(value, 64)
    return value if value and _HASH.fullmatch(value) else None
def _section(metadata):
    heading = citation.safe_citation_text(metadata.get("section_heading"), 200)
    raw_path = metadata.get("section_path")
    if not isinstance(raw_path, list) or not 1 <= len(raw_path) <= 6:
        return None, None
    path = [citation.safe_citation_text(part, 200) for part in raw_path]
    return (heading, path) if heading and all(path) and heading == path[-1] else (None, None)


def format_sources(documents: object) -> list[dict]:
    if not documents:
        return []
    if isinstance(documents, dict):
        documents = [documents] if any(key in documents for key in _SINGLE_KEYS) else [documents[key] for key in sorted(documents, key=str)]
    if not isinstance(documents, list):
        return []
    sources = []
    for document in documents:
        if not isinstance(document, dict) or not document:
            continue
        metadata = document.get("metadata", document)
        if not isinstance(metadata, dict) or not metadata:
            continue
        name = (citation.safe_source_name(metadata.get("original_source_name"))
                or citation.safe_source_name(metadata.get("source")))
        heading, path = _section(metadata)
        source = {field: citation.safe_citation_text(metadata.get(field)) for field in _TEXT_FIELDS}
        source.update({
            "title": citation.safe_citation_title(metadata.get("title"), name), "original_source_name": name, "content_hash": _hash(metadata.get("content_hash")),
            "chunk_index": _integer(metadata.get("chunk_index")), "fragment_hash": _hash(metadata.get("fragment_hash")), "section_heading": heading, "section_path": path,
            "page_start": _integer(metadata.get("page_start"), 1), "page_end": _integer(metadata.get("page_end"), 1),
            "url": citation.normalize_citation_url(metadata.get("url")), "doi": citation.normalize_doi(metadata.get("doi")), "isbn": citation.normalize_isbn(metadata.get("isbn")),
            "publication_date": citation.safe_citation_text(metadata.get("publication_date"), 64, no_whitespace=True), "review_date": citation.safe_citation_text(metadata.get("review_date"), 64, no_whitespace=True),
            "evidence_level": citation.safe_citation_text(metadata.get("evidence_level"), 100), "source": name,
            "score": document.get("score", 0.0), "retrieval_mode": citation.safe_citation_text(document.get("retrieval_mode", "dense"), 32),
            "score_type": citation.safe_citation_text(document.get("score_type", "cosine"), 32),
        })
        if not isinstance(source["score"], (int, float)) or not math.isfinite(source["score"]):
            source["score"] = None
        sources.append(source)
    return sources
