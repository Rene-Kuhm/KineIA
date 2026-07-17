import json
from hashlib import sha256
from math import isfinite
from uuid import UUID

from qdrant_client.models import PointStruct, UpdateMode


class _Digest:
    def __init__(self):
        self.value, self.first = sha256(), True
        self.value.update(b"[")
    def add(self, item) -> None:
        if not self.first:
            self.value.update(b",")
        encoded = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.value.update(encoded.encode())
        self.first = False
    def finish(self) -> str:
        self.value.update(b"]")
        return self.value.hexdigest()
def _valid_dense(vector, dimensions: int) -> bool:
    return (isinstance(vector, list) and len(vector) == dimensions
            and all(type(value) in (int, float) and isfinite(value) for value in vector))
def _valid_sparse(vector) -> bool:
    indices, values = getattr(vector, "indices", None), getattr(vector, "values", None)
    return bool(isinstance(indices, list) and isinstance(values, list) and indices
                and len(indices) == len(values)
                and all(type(index) is int and index >= 0 for index in indices)
                and len(indices) == len(set(indices))
                and all((type(value) is int and abs(value) <= 1.7976931348623157e308)
                        or (type(value) is float and isfinite(value)) for value in values))
def _validate(legacy: str, hybrid: str, page_size: int) -> None:
    if legacy == hybrid:
        raise ValueError("legacy and hybrid collections must be distinct")
    if not 1 <= page_size <= 1000:
        raise ValueError("page_size must be between 1 and 1000")
def _key(point_id):
    if type(point_id) is int:
        return 0, point_id
    if type(point_id) is str:
        parsed = UUID(point_id)
        if str(parsed) == point_id.lower():
            return 1, parsed.int
    raise ValueError("unsupported point ID")
def _stream(client, collection: str, page_size: int, state: dict):
    offset = previous = None
    while True:
        page, offset = client.scroll(collection_name=collection, limit=page_size, offset=offset,
                                     with_payload=True, with_vectors=True)
        for record in page:
            key = _key(record.id)
            if ((state["kind"] is not None and state["kind"] != key[0])
                    or (previous is not None and key <= previous)):
                raise ValueError("unsupported point ordering")
            state["kind"], previous = key[0], key
            state["count"] += 1
            state["ids"].add(record.id)
            state["payloads"].add([record.id, record.payload])
            yield key, record
        if offset is None:
            return
def _state() -> dict:
    return {"count": 0, "kind": None, "ids": _Digest(), "payloads": _Digest()}
def backfill_hybrid(
    client, *, legacy: str, hybrid: str, dense_name: str, sparse_name: str,
    dimensions: int, encoder, page_size: int = 100, offset=None, max_pages: int | None = None,
) -> dict:
    _validate(legacy, hybrid, page_size)
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be positive")
    processed = submitted = pages = 0
    errors: list[dict] = []
    while True:
        records, next_offset = client.scroll(
            collection_name=legacy, limit=page_size, offset=offset,
            with_payload=True, with_vectors=True,
        )
        points = []
        for record in records:
            processed += 1
            payload, dense = record.payload, record.vector
            text = payload.get("text") if isinstance(payload, dict) else None
            if not isinstance(text, str) or not text.strip():
                errors.append({"id": record.id, "code": "missing_text"})
                continue
            if not _valid_dense(dense, dimensions):
                errors.append({"id": record.id, "code": "malformed_dense"})
                continue
            try:
                sparse = encoder.encode(text)
                if not _valid_sparse(sparse):
                    raise ValueError("invalid sparse vector")
            except Exception:
                errors.append({"id": record.id, "code": "sparse_encoding"})
                continue
            points.append(PointStruct(id=record.id, payload=payload,
                                      vector={dense_name: dense, sparse_name: sparse}))
        if points:
            client.upsert(collection_name=hybrid, points=points, wait=True,
                          update_mode=UpdateMode.INSERT_ONLY)
            submitted += len(points)
        pages += 1
        offset = next_offset
        if offset is None or (max_pages is not None and pages >= max_pages):
            return {"processed": processed, "submitted": submitted,
                    "next_offset": offset, "errors": errors}
def verify_hybrid(
    client, *, legacy: str, hybrid: str, dense_name: str, sparse_name: str,
    dimensions: int, page_size: int = 100, sample_limit: int = 100,
) -> dict:
    _validate(legacy, hybrid, page_size)
    if not 1 <= sample_limit <= 1000:
        raise ValueError("sample_limit must be between 1 and 1000")
    old_state, new_state = _state(), _state()
    old_stream = _stream(client, legacy, page_size, old_state)
    new_stream = _stream(client, hybrid, page_size, new_state)
    samples = {kind: [] for kind in ("missing", "orphan", "errors")}
    totals = {kind: 0 for kind in samples}
    def add(kind, value):
        totals[kind] += 1
        if len(samples[kind]) < sample_limit:
            samples[kind].append(value)
    dense_matched = sparse_matched = 0
    try:
        old_item, new_item = next(old_stream, None), next(new_stream, None)
        if old_item and new_item and old_item[0][0] != new_item[0][0]:
            raise ValueError("mixed point ID types")
        while old_item or new_item:
            if new_item is None or (old_item and old_item[0] < new_item[0]):
                add("missing", old_item[1].id)
                old_item = next(old_stream, None)
            elif old_item is None or new_item[0] < old_item[0]:
                add("orphan", new_item[1].id)
                new_item = next(new_stream, None)
            else:
                point_id, old, new = old_item[1].id, old_item[1], new_item[1]
                vectors = new.vector if isinstance(new.vector, dict) else {}
                if old.payload != new.payload:
                    add("errors", {"id": point_id, "code": "payload_mismatch"})
                if _valid_dense(old.vector, dimensions) and vectors.get(dense_name) == old.vector:
                    dense_matched += 1
                else:
                    add("errors", {"id": point_id, "code": "dense_mismatch"})
                sparse = vectors.get(sparse_name)
                if _valid_sparse(sparse):
                    sparse_matched += 1
                else:
                    code = "missing_sparse" if sparse is None else "malformed_sparse"
                    add("errors", {"id": point_id, "code": code})
                old_item, new_item = next(old_stream, None), next(new_stream, None)
    except (TypeError, ValueError):
        add("errors", {"id": None, "code": "unsupported_id_order"})
    total = old_state["count"]
    def coverage(matched):
        return {"matched": matched, "total": total,
                "percent": round(100 * matched / total, 6) if total else 100.0}
    report = {
        "counts": {"legacy": old_state["count"], "v2": new_state["count"]},
        "id_digests": {"legacy": old_state["ids"].finish(),
                       "v2": new_state["ids"].finish()},
        "payload_digests": {"legacy": old_state["payloads"].finish(),
                            "v2": new_state["payloads"].finish()},
        "dense_coverage": coverage(dense_matched),
        "sparse_coverage": coverage(sparse_matched),
        "missing_ids": samples["missing"], "orphan_ids": samples["orphan"],
        "errors": samples["errors"], "discrepancy_counts": totals,
        "truncated": {"missing_ids": totals["missing"] > len(samples["missing"]),
                      "orphan_ids": totals["orphan"] > len(samples["orphan"]),
                      "errors": totals["errors"] > len(samples["errors"])},
    }
    report["ready"] = (
        report["counts"]["legacy"] == report["counts"]["v2"] and total > 0
        and report["id_digests"]["legacy"] == report["id_digests"]["v2"]
        and report["payload_digests"]["legacy"] == report["payload_digests"]["v2"]
        and report["dense_coverage"]["percent"] == 100.0
        and report["sparse_coverage"]["percent"] == 100.0
        and not any(totals.values())
    )
    return report
