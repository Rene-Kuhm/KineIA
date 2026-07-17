from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from app.db.hybrid_backfill import backfill_hybrid, verify_hybrid
from qdrant_client.models import SparseVector, UpdateMode


def _point(point_id, payload, vector):
    return SimpleNamespace(id=point_id, payload=payload, vector=vector)
def test_backfill_preserves_legacy_data_and_uses_atomic_insert_only():
    client, encoder = MagicMock(), MagicMock()
    record = _point(7, {"text": "Rodilla", "area": "trauma"}, [0.1, 0.2])
    client.scroll.return_value = ([record], None)
    encoder.encode.return_value = SparseVector(indices=[3], values=[0.7])
    report = backfill_hybrid(client, legacy="legacy", hybrid="v2", dense_name="dense",
                             sparse_name="sparse", dimensions=2, encoder=encoder,
                             page_size=25)
    point = client.upsert.call_args.kwargs["points"][0]
    assert (point.id, point.payload, client.upsert.call_args.kwargs["update_mode"]) == (
        record.id, record.payload, UpdateMode.INSERT_ONLY)
    assert point.vector == {"dense": record.vector, "sparse": encoder.encode.return_value}
    assert client.scroll.call_args.kwargs | {"collection_name": "legacy"} == {
        "collection_name": "legacy", "limit": 25, "offset": None,
        "with_payload": True, "with_vectors": True,
    }
    assert report == {"processed": 1, "submitted": 1, "next_offset": None, "errors": []}
def test_backfill_reports_missing_text_and_malformed_dense_without_writing():
    client, encoder = MagicMock(), MagicMock()
    client.scroll.return_value = ([
        _point(1, {"text": " "}, [0.1, 0.2]), _point(2, {"text": "valid"}, [0.1]),
    ], None)
    report = backfill_hybrid(client, legacy="legacy", hybrid="v2", dense_name="dense",
                             sparse_name="sparse", dimensions=2, encoder=encoder)
    assert report["submitted"] == 0
    assert report["errors"] == [{"id": 1, "code": "missing_text"},
                                {"id": 2, "code": "malformed_dense"}]
    assert not encoder.encode.called and not client.upsert.called
def test_verifier_requires_exact_complete_matching_collections():
    client = MagicMock()
    payload = {"text": "Rodilla", "area": "trauma"}
    legacy = [_point(i, payload, [0.1, 0.2]) for i in (7, 8)]
    hybrid = [_point(i, payload, {"dense": [0.1, 0.2],
              "sparse": SparseVector(indices=[3], values=[0.7])}) for i in (7, 8)]
    calls = []
    def scroll(collection_name, offset=None, **_kwargs):
        calls.append(collection_name)
        index = offset or 0
        return [[legacy, hybrid][collection_name == "v2"][index]], index + 1 if index == 0 else None
    client.scroll.side_effect = scroll
    report = verify_hybrid(client, legacy="legacy", hybrid="v2",
                           dense_name="dense", sparse_name="sparse", dimensions=2, page_size=10)
    assert report["counts"] == {"legacy": 2, "v2": 2} and calls[:2] == ["legacy", "v2"]
    assert all(len(set(d.values())) == 1 for d in (report["id_digests"], report["payload_digests"]))
    assert report["dense_coverage"] == report["sparse_coverage"] == {
        "matched": 2, "total": 2, "percent": 100.0}
    assert report["missing_ids"] == report["orphan_ids"] == report["errors"] == []
    assert report["ready"] is True
    client.scroll.side_effect = [([_point("unsupported", payload, [0.1, 0.2])], None)]
    failed = verify_hybrid(client, legacy="legacy", hybrid="v2", dense_name="dense",
                           sparse_name="sparse", dimensions=2)
    assert failed["ready"] is False and failed["errors"][-1]["code"] == "unsupported_id_order"
@pytest.mark.parametrize(("indices", "values"), [
    ([], []), ([1], []), ([-1], [1.0]), ([1.5], [1.0]), ([1, 1], [1.0, 2.0]),
    ([True], [1.0]), ([1], [float("nan")]), ([1], [float("inf")]), ([1], [True]),
    ([1], ["x"]), ([[1]], [1.0]), ([1], [10**10000]),
])
def test_verifier_rejects_malformed_sparse_vectors(indices, values):
    client = MagicMock()
    old = _point(7, {"text": "x"}, [0.1, 0.2])
    sparse = SimpleNamespace(indices=indices, values=values)
    new = _point(7, old.payload, {"dense": old.vector, "sparse": sparse})
    client.scroll.side_effect = [([old], None), ([new], None)]
    report = verify_hybrid(client, legacy="legacy", hybrid="v2", dense_name="dense",
                           sparse_name="sparse", dimensions=2)
    assert report["ready"] is False and report["sparse_coverage"]["matched"] == 0
    assert {error["code"] for error in report["errors"]} == {"malformed_sparse"}
def test_discrepancy_samples_are_bounded_without_losing_totals():
    client = MagicMock()
    payload, sparse = {"text": "x"}, SimpleNamespace(indices=[], values=[])
    old = [_point(i, payload, [0.1, 0.2]) for i in range(1, 7)]
    new = [_point(i, payload, {"dense": [0.1, 0.2], "sparse": sparse}) for i in range(1, 6)]
    new += [_point(i, payload, {}) for i in range(7, 12)]
    client.scroll.side_effect = [(old, None), (new, None)]
    report = verify_hybrid(client, legacy="legacy", hybrid="v2", dense_name="dense",
                           sparse_name="sparse", dimensions=2, sample_limit=2)
    assert report["discrepancy_counts"] == {"missing": 1, "orphan": 5, "errors": 5}
    assert report["truncated"] == {"missing_ids": False, "orphan_ids": True, "errors": True}
    sample_sizes = map(len, (report["missing_ids"], report["orphan_ids"], report["errors"]))
    assert tuple(sample_sizes) == (1, 2, 2) and report["ready"] is False
