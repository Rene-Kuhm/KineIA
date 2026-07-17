# ruff: noqa: E302, E305, E501, E701, E702
import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping

from app.services.rag.citations import format_sources

MAX_EVIDENCE_ITEMS = 5
MAX_FRAGMENT_BYTES = 8 * 1024
MAX_EVIDENCE_BYTES = 32 * 1024
MAX_ANSWER_BYTES = 16 * 1024
MAX_ENVELOPE_BYTES = 64 * 1024
STATUSES = frozenset({
    "verified", "insufficient_evidence", "invalid_citations", "llm_unavailable",
    "legacy_unverified",
})
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_MARKER = re.compile(r"\[C([1-5])\]")
_CANDIDATE = re.compile(r"\[(?:[^\w\[\]]|_)*[CcᴄСсϹϲΣςᏟꓚᑕⲤⲥꮯ](?:[^\w\[\]]|_)*\d")  # Compact reviewed C-shaped confusables plus NFKD forms.
_ENVELOPE_KEYS = {"schema_version", "citation_status", "items"}
_ITEM_KEYS = {
    "citation_id", "fragment", "rerank_score", "source_id", "source_version",
    "source_version_id", "title", "original_source_name", "content_hash", "chunk_index",
    "fragment_hash", "section_heading", "section_path", "page_start", "page_end", "url",
    "doi", "isbn", "publication_date", "review_date", "evidence_level", "source", "score",
    "retrieval_mode", "score_type",
}
_OPTIONAL_TEXT = ("source_version", "title", "original_source_name", "content_hash", "section_heading", "url", "doi", "isbn", "publication_date", "review_date", "evidence_level", "source")
class CitationError(ValueError):
    pass
def _exact(value, *types):
    return type(value) in types
def _unsafe(char):
    return (unicodedata.category(char).startswith("C") and char not in "\r\n\t") or char in "\u2028\u2029"
def _safe_fragment(value):
    if not _exact(value, str) or not value.strip(): raise CitationError("fragment must be non-empty text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise CitationError("fragment must be valid UTF-8") from error
    if len(encoded) > MAX_FRAGMENT_BYTES: raise CitationError("fragment exceeds 8 KiB")
    if any(_unsafe(char) for char in value): raise CitationError("fragment contains unsafe control text")
    return encoded
def _finite(value):
    try: return _exact(value, int, float) and math.isfinite(value)
    except (OverflowError, ValueError): return False
def prepare_evidence(documents):
    if type(documents) is not list: raise CitationError("documents must be a list")
    prepared, identities, total = [], set(), 0
    for position, document in enumerate(documents[:MAX_EVIDENCE_ITEMS], 1):
        if (type(document) is not dict or any(type(key) is not str for key in document) or type(document.get("metadata")) is not dict
                or any(type(key) is not str for key in document["metadata"])):
            raise CitationError("candidate metadata is malformed")
        metadata = document["metadata"]
        if any(metadata.get(field) is not None and type(metadata[field]) is not str for field in _OPTIONAL_TEXT): raise CitationError("candidate text metadata is malformed")
        if metadata.get("section_path") is not None and (type(metadata["section_path"]) is not list or any(type(part) is not str for part in metadata["section_path"])): raise CitationError("candidate section path is malformed")
        if any(metadata.get(field) is not None and type(metadata[field]) is not int for field in ("page_start", "page_end")): raise CitationError("candidate page locator is malformed")
        identity = (metadata.get("source_id"), metadata.get("source_version_id"),
                    metadata.get("chunk_index"))
        if (not all(_exact(value, str) and value.strip() == value for value in identity[:2])
                or not _exact(identity[2], int)
                or identity[2] < 0):
            raise CitationError("candidate identity is malformed")
        if identity in identities: raise CitationError("duplicate candidate identity")
        identities.add(identity)
        encoded = _safe_fragment(document.get("text"))
        total += len(encoded)
        if total > MAX_EVIDENCE_BYTES: raise CitationError("evidence exceeds 32 KiB")
        stored_hash = metadata.get("fragment_hash")
        if not _exact(stored_hash, str) or not _HASH.fullmatch(stored_hash): raise CitationError("stored fragment hash is malformed")
        if hashlib.sha256(encoded).hexdigest() != stored_hash: raise CitationError("stored fragment hash does not match")
        if not all(_finite(document.get(field)) for field in ("score", "rerank_score")): raise CitationError("score provenance is malformed")
        if not all(_exact(document.get(field), str) for field in ("retrieval_mode", "score_type")): raise CitationError("retrieval provenance is malformed")
        source = format_sources([document])[0]
        if (source["source_id"] != identity[0]
                or source["source_version_id"] != identity[1]
                or source["chunk_index"] != identity[2]
                or source["fragment_hash"] != stored_hash):
            raise CitationError("candidate identity metadata is not canonical")
        for field in ("source_version", "content_hash", "url", "doi", "isbn",
                      "publication_date", "review_date", "evidence_level"):
            if metadata.get(field) is not None and source[field] is None:
                raise CitationError(f"candidate {field} is malformed")
        section_present = any(metadata.get(field) is not None
                              for field in ("section_heading", "section_path"))
        pages_present = any(metadata.get(field) is not None
                            for field in ("page_start", "page_end"))
        if (section_present and (source["section_heading"] is None
                                 or source["section_path"] is None)):
            raise CitationError("candidate locator is malformed")
        if (pages_present and (source["page_start"] is None or source["page_end"] is None)
                or source["page_start"] is not None
                and source["page_start"] > source["page_end"]):
            raise CitationError("candidate page locator is malformed")
        if source["retrieval_mode"] is None or source["score_type"] is None:
            raise CitationError("retrieval provenance is malformed")
        prepared.append(source | {"citation_id": f"C{position}", "fragment": document["text"],
                                  "rerank_score": document["rerank_score"]})
    return prepared
def _invalid(status="invalid_citations"):
    return {"schema_version": 2, "citation_status": status, "items": []}
def _references(answer):
    matches = list(_MARKER.finditer(answer))
    view = "".join(char for char in unicodedata.normalize("NFKD", answer) if not _unsafe(char) and not unicodedata.category(char).startswith("M"))
    candidates = _CANDIDATE.findall(view)
    adjacent = any(answer[match.start() - 1:match.start()] == "[" or answer[match.end():match.end() + 1] == "]" for match in matches)
    if len(candidates) != len(matches) or adjacent or re.search(r"\[[ \t]*[Cc][ \t]*\]", view) or re.search(r"(?<!\[)[Cc]\d+\]", view):
        return None
    return [f"C{match.group(1)}" for match in matches]
def validate_answer_citations(answer, evidence):
    if not _exact(answer, str):
        return _invalid()
    try:
        if len(answer.encode("utf-8")) > MAX_ANSWER_BYTES:
            return _invalid()
    except UnicodeEncodeError:
        return _invalid()
    authorized = _authorize_evidence(evidence)
    if not authorized:
        return _invalid("insufficient_evidence")
    references = _references(answer)
    if (not answer.strip() or not references
            or any(ref not in authorized for ref in references)):
        return _invalid()
    unique = list(dict.fromkeys(references))
    return {"schema_version": 2, "citation_status": "verified",
            "items": [authorized[ref] for ref in unique]}
def _validate_item(item):
    if type(item) is not dict or any(type(key) is not str for key in item) or set(item) != _ITEM_KEYS:
        raise CitationError("citation item fields are malformed")
    if any(item[field] is not None and type(item[field]) is not str for field in _OPTIONAL_TEXT):
        raise CitationError("citation text metadata is malformed")
    if item["section_path"] is not None and (type(item["section_path"]) is not list or any(type(part) is not str for part in item["section_path"])):
        raise CitationError("citation section path is malformed")
    if not _exact(item["citation_id"], str) or not re.fullmatch(r"C[1-5]", item["citation_id"]):
        raise CitationError("citation ID is malformed")
    encoded = _safe_fragment(item["fragment"])
    if (not _exact(item["fragment_hash"], str) or not _HASH.fullmatch(item["fragment_hash"])
            or hashlib.sha256(encoded).hexdigest() != item["fragment_hash"]):
        raise CitationError("citation fragment hash does not match")
    if not all(_finite(item[field]) for field in ("score", "rerank_score")):
        raise CitationError("citation score is malformed")
    required_text = ("source_id", "source_version_id", "retrieval_mode", "score_type")
    if (not all(_exact(item[field], str) and item[field] for field in required_text)
            or not _exact(item["chunk_index"], int)
            or item["chunk_index"] < 0):
        raise CitationError("citation identity is malformed")
    pages = (item["page_start"], item["page_end"])
    if ((pages[0] is None) != (pages[1] is None)
            or pages[0] is not None and (any(type(page) is not int or page < 1 for page in pages)
                                         or pages[0] > pages[1])):
        raise CitationError("citation page locator is malformed")
    canonical = format_sources([item])[0]
    if any(item[field] != value for field, value in canonical.items()):
        raise CitationError("citation metadata is not canonical")
    return len(encoded)
def _authorize_evidence(evidence):
    if type(evidence) is not list or len(evidence) > MAX_EVIDENCE_ITEMS:
        raise CitationError("authorized evidence is malformed")
    authorized, identities, total = {}, set(), 0
    for position, item in enumerate(evidence, 1):
        total += _validate_item(item)
        identity = (item["source_id"], item["source_version_id"], item["chunk_index"])
        if item["citation_id"] != f"C{position}" or identity in identities:
            raise CitationError("authorized evidence identity or order is malformed")
        authorized[item["citation_id"]] = item
        identities.add(identity)
    if total > MAX_EVIDENCE_BYTES:
        raise CitationError("authorized evidence exceeds 32 KiB")
    return authorized
def _validate_v2(envelope):
    if type(envelope) is not dict or any(type(key) is not str for key in envelope) or set(envelope) != _ENVELOPE_KEYS:
        raise CitationError("citation envelope fields are malformed")
    version, status, items = envelope["schema_version"], envelope["citation_status"], envelope["items"]
    if (type(version) is not int or version != 2 or type(status) is not str
            or status not in STATUSES or status == "legacy_unverified"):
        raise CitationError("citation envelope version or status is invalid")
    if type(items) is not list or len(items) > MAX_EVIDENCE_ITEMS:
        raise CitationError("citation items are malformed")
    if status == "verified" and not items:
        raise CitationError("verified envelopes require citation items")
    if status != "verified" and items:
        raise CitationError("unverified envelopes cannot contain items")
    seen, identities, total = set(), set(), 0
    for item in items:
        total += _validate_item(item)
        identity = (item["source_id"], item["source_version_id"], item["chunk_index"])
        if item["citation_id"] in seen or identity in identities:
            raise CitationError("duplicate citation ID or identity")
        seen.add(item["citation_id"])
        identities.add(identity)
    if total > MAX_EVIDENCE_BYTES:
        raise CitationError("citation fragments exceed 32 KiB")
    return envelope
def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CitationError("duplicate JSON field")
        result[key] = value
    return result
def _dump(value):
    try: return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, OverflowError, RecursionError) as error: raise CitationError("citation envelope JSON is malformed") from error
def _plain(value, depth=0, state=None):
    state = state or [256, set()]
    if depth > 4 or state[0] < 1:
        raise CitationError("legacy citation nesting is malformed")
    state[0] -= 1
    if not isinstance(value, (Mapping, list)): return value
    marker = id(value)
    if marker in state[1]: raise CitationError("legacy citation cycle")
    state[1].add(marker)
    try:
        if isinstance(value, Mapping): return {key: _plain(item, depth + 1, state) for key, item in value.items()}
        return [_plain(item, depth + 1, state) for item in value]
    finally: state[1].remove(marker)
def normalize_citation_envelope(value):
    if value is not None and not isinstance(value, (Mapping, list)):
        raise CitationError("citation persistence value is malformed")
    plain = type(value) is dict
    if plain and not any(type(key) is not str for key in value):
        version = value.get("schema_version")
        if type(version) is int and version == 2:
            return _validate_v2(value)
        if type(version) is int and version == 1 and (set(value) != _ENVELOPE_KEYS
                or type(value.get("citation_status")) is not str or value.get("citation_status") != "legacy_unverified"
                or type(value.get("items")) is not list):
            raise CitationError("legacy citation envelope is malformed")
        if type(version) is int and version == 1: value = value["items"]
    try: value = _plain(value)
    except Exception: value = None
    if not plain and type(value) is dict and all(type(key) is str for key in value) and type(value.get("schema_version")) is int and value.get("schema_version") in (1, 2):
        raise CitationError("citation envelope must be a plain object")
    try: items = format_sources(value)
    except Exception: items = []
    if len(items) > MAX_EVIDENCE_ITEMS:
        raise CitationError("legacy citation envelope has too many items")
    envelope = {"schema_version": 1, "citation_status": "legacy_unverified", "items": items}
    encoded = _dump(envelope)
    if len(encoded.encode("utf-8")) > MAX_ENVELOPE_BYTES:
        raise CitationError("legacy citation envelope exceeds 64 KiB")
    return envelope
def serialize_citation_envelope(envelope):
    normalized = normalize_citation_envelope(envelope)
    encoded = _dump(normalized)
    if len(encoded.encode("utf-8")) > MAX_ENVELOPE_BYTES:
        raise CitationError("citation envelope exceeds 64 KiB")
    return encoded
def read_citation_envelope(value):
    if type(value) is not str:
        raise CitationError("serialized citation envelope must be text")
    try:
        if len(value.encode("utf-8")) > MAX_ENVELOPE_BYTES:
            raise CitationError("citation envelope exceeds 64 KiB")
        parsed = json.loads(value, object_pairs_hook=_unique_object)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise CitationError("citation envelope JSON is malformed") from error
    normalized = normalize_citation_envelope(parsed)
    if serialize_citation_envelope(normalized) != value:
        raise CitationError("citation envelope is not canonical")
    return normalized
