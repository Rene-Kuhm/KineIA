# ruff: noqa: E302, E305, E501, E701, E702, I001
import copy
import hashlib
from types import MappingProxyType
import pytest
from app.services.rag.citations import format_sources
from app.services.rag.response_citations import (
    CitationError,
    normalize_citation_envelope,
    prepare_evidence,
    read_citation_envelope,
    serialize_citation_envelope,
    validate_answer_citations,
)
def _bomb(base): return type("Bomb", (base,), {"__eq__": lambda self, other: (_ for _ in ()).throw(RuntimeError("boom"))})
def _document(text="Evidence", index=0, **changes):
    metadata = {
        "source_id": "doi:10.1000/guide",
        "source_version": "2026",
        "source_version_id": "v1",
        "chunk_index": index,
        "fragment_hash": hashlib.sha256(text.encode()).hexdigest(),
        "title": "Guide",
        "original_source_name": "guide.md",
        "section_heading": "Exercise",
        "section_path": ["Knee", "Exercise"],
        "publication_date": "2025-04-01",
        "review_date": "2026-07-16",
        "evidence_level": "guideline",
        "url": "https://example.org/guide",
        "doi": "10.1000/guide",
        "isbn": "9781402894626",
    }
    metadata.update(changes.pop("metadata", {}))
    return {"text": text, "metadata": metadata, "score": 0.8,
            "rerank_score": 0.9, "retrieval_mode": "hybrid", "score_type": "rrf"} | changes
def test_prepares_exact_evidence_and_emits_only_first_referenced_items():
    evidence = prepare_evidence([_document("First", 0), _document("Second", 1)])
    assert [item["citation_id"] for item in evidence] == ["C1", "C2"]
    assert evidence[0]["fragment"] == "First"
    envelope = validate_answer_citations("Second [C2], first [C1], second [C2].", evidence)
    assert envelope["citation_status"] == "verified"
    assert [item["citation_id"] for item in envelope["items"]] == ["C2", "C1"]
def test_rejects_unknown_or_marker_like_malformed_citations():
    evidence = prepare_evidence([_document()])
    for answer in ("Unknown [C6], valid [C1].", "Padded [ C1 ] and [C1].", "Bare [C] [C1].",
                   "Lowercase [c1] and [C1].", "Broken [C1, C2] and [C1].",
                   "Unicode [Ｃ1] and [C1].", "Unclosed [C1 and [C1].",
                   "Extra [C1]] and [C1].", "Spaced [C 1] [C1].", "Zero [C0] [C1].",
                   "Leading zero [C01] [C1].", "Nested [foo [C6]] [C1].", "Nested [foo [C0]] [C1].",
                   "Hidden [C\u200b6] [C1].", "Bidi [C\u202e6] [C1].", "Isolate [C\u20666] [C1].", "Combining [C\u03016] [C1].", "Variation [C\ufe0f6] [C1].", "Joiner [C\u034f6] [C1].", "Nested [foo [C\u03016]] [C1].", "Dash [C-6] [C1].", "Under [C_6] [C1].", "Colon [C:6] [C1].", "Nested [foo [C-6]] [C1].", "Prefix [.C-6] [C1].", "Spaced [ - C - 6 ] [C1].", "Nested [foo [.C-6]] [C1].", "Mixed [foo [.\u200bC\u0301-6]] [C1].", *(answer for char in "ᴄСсϹϲᏟꓚᑕⲤⲥꮯ" for answer in (f"Confusable [{char}6] [C1].", f"Nested [foo [{char}-6]] [C1].", f"Unclosed [{char}6 and [C1].", f"Trailing [{char}6]] [C1]."))):
        assert validate_answer_citations(answer, evidence)["citation_status"] == "invalid_citations"
    assert all(validate_answer_citations(answer, evidence)["citation_status"] == "verified" for answer in ("[clinical grade 2] [C1]", "[cafe\u0301 grade 2] [C1]", "[C-reactive protein 6] [C1]", "[°C] [C1]", "[℃] [C1]", "[C++] [C1]", "[C#] [C1]"))
    assert validate_answer_citations("[" * (16 * 1024 - 1), evidence)["citation_status"] == "invalid_citations"
def test_version_two_envelopes_serialize_deterministically_and_read_strictly():
    envelope = validate_answer_citations("Supported [C1].", prepare_evidence([_document()]))
    encoded = serialize_citation_envelope(envelope)
    assert encoded == serialize_citation_envelope(envelope)
    assert read_citation_envelope(encoded) == envelope
    with pytest.raises(CitationError): read_citation_envelope(type("S", (str,), {})(encoded))
    for malformed in (
        encoded[:-1] + ',"extra":1}',
        encoded.replace('"verified"', '"unknown"'),
        '{"schema_version":2,"schema_version":2,"citation_status":"verified","items":[]}',
        "9" * 5000, "[" * 10000 + "]" * 10000,
    ):
        with pytest.raises(CitationError): read_citation_envelope(malformed)
def test_verified_envelopes_reject_noncanonical_metadata_and_wrong_types():
    envelope = validate_answer_citations("Supported [C1].", prepare_evidence([_document()])); s_type = type("S", (str,), {}); i_type = type("I", (int,), {}); f_type = type("F", (float,), {}); d_type = type("D", (dict,), {}); l_type = type("L", (list,), {}); b_str, b_int, b_list = _bomb(str), _bomb(int), _bomb(list)
    for field, value in (("original_source_name", r"C:\private\guide.md"),
                         ("title", r"C:\private\guide.md"), ("url", "https:evil.test"),
                         ("doi", "10.1000/GUIDE"), ("publication_date", "2025-01-01\x00"),
                         ("source_id", []), ("citation_id", s_type("C1")), ("fragment", s_type("Evidence")),
                         ("source_id", s_type("doi:10.1000/guide")), ("source_version_id", s_type("v1")),
                         ("retrieval_mode", s_type("hybrid")), ("chunk_index", i_type(0)), ("score", f_type(0.8)), ("score", 10 ** 1000),
                         ("rerank_score", f_type(0.9)), *((field, s_type(envelope["items"][0][field] or "0" * 64)) for field in ("source_version", "title", "original_source_name", "content_hash", "section_heading", "url", "doi", "isbn", "publication_date", "review_date", "evidence_level", "source")),
                         ("section_path", l_type(["Knee", "Exercise"])), ("section_path", ["Knee", s_type("Exercise")]), ("source_id", b_str("doi:10.1000/guide")), ("chunk_index", b_int(0)), ("page_start", b_int(1)), ("section_path", b_list(["Knee", "Exercise"]))):
        changed = copy.deepcopy(envelope); changed["items"][0][field] = value
        with pytest.raises(CitationError): serialize_citation_envelope(changed)
    for version, status, items in ((2, [], envelope["items"]), (2, s_type("verified"), envelope["items"]), (2, b_str("verified"), envelope["items"]), (2, "verified", b_list(envelope["items"]))):
        changed = copy.deepcopy(envelope); changed["schema_version"] = version; changed["citation_status"] = status; changed["items"] = items
        with pytest.raises(CitationError): serialize_citation_envelope(changed)
    for version in (2.0, True, b_int(2)): changed = copy.deepcopy(envelope); changed["schema_version"] = version; assert normalize_citation_envelope(changed)["citation_status"] == "legacy_unverified"
    assert validate_answer_citations(s_type("Supported [C1]."), prepare_evidence([_document()]))["citation_status"] == "invalid_citations"
    for changes in ({"text": s_type("Evidence")}, {"metadata": {"source_id": s_type("doi:10.1000/guide")}},
                    {"metadata": {"source_version_id": s_type("v1")}}, {"metadata": {"chunk_index": i_type(0)}},
                    {"score": f_type(0.8)}, {"rerank_score": f_type(0.9)}, {"retrieval_mode": s_type("hybrid")}, *({"metadata": {field: s_type(_document()["metadata"].get(field) or "x")}} for field in ("source_version", "title", "original_source_name", "content_hash", "section_heading", "url", "doi", "isbn", "publication_date", "review_date", "evidence_level", "source")),
                    {"metadata": {"section_path": l_type(["Knee", "Exercise"])}}, {"metadata": {"section_path": ["Knee", s_type("Exercise")]}}, {"metadata": {"page_start": i_type(1), "page_end": 1}}, {"score": 10 ** 1000}):
        with pytest.raises(CitationError): prepare_evidence([_document(**changes)])
    for document in (d_type(_document()), _document() | {"metadata": d_type(_document()["metadata"])}):
        with pytest.raises(CitationError): prepare_evidence([document])
def test_v2_rejects_aggregate_fragment_budget_and_legacy_accepts_mappings():
    items = [prepare_evidence([_document("x" * 7000, index)])[0] for index in range(5)]
    for index, item in enumerate(items, 1): item["citation_id"] = f"C{index}"
    with pytest.raises(CitationError):
        serialize_citation_envelope({"schema_version": 2, "citation_status": "verified", "items": items})
    legacy = [MappingProxyType({"metadata": MappingProxyType(_document()["metadata"])})]
    assert normalize_citation_envelope(legacy) == normalize_citation_envelope([{"metadata": _document()["metadata"]}])
    with pytest.raises(CitationError): normalize_citation_envelope(MappingProxyType({"schema_version": 2}))
    broken = type("Broken", (dict,), {"items": lambda self: (_ for _ in ()).throw(RuntimeError())})(); cycle = []; cycle.append(cycle)
    assert normalize_citation_envelope(broken)["items"] == normalize_citation_envelope(cycle)["items"] == []
    assert normalize_citation_envelope([{str(n): n for n in range(64)} for _ in range(64)])["items"] == []
def test_legacy_shapes_normalize_unverified_without_inventing_fragments():
    legacy = _document()["metadata"]; b_str, b_list = _bomb(str), _bomb(list)
    expected = format_sources(legacy)
    for value in (legacy, [legacy], {"a": legacy, "bad": 7}):
        envelope = normalize_citation_envelope(value)
        assert envelope == {"schema_version": 1, "citation_status": "legacy_unverified",
                            "items": expected}
        assert "fragment" not in envelope["items"][0]
    verified = validate_answer_citations("Supported [C1].", prepare_evidence([_document()])); collision = {"schema_version": "2025", "citation_status": "paper", "source": "guide.md"}
    assert format_sources(verified) == []; assert format_sources(collision)[0]["source"] == "guide.md"; assert normalize_citation_envelope(collision)["citation_status"] == "legacy_unverified"
    for version, status, items in ((1, type("S", (str,), {})("legacy_unverified"), []), (1, b_str("legacy_unverified"), []), (1, "legacy_unverified", b_list()), (2, "paper", [])):
        with pytest.raises(CitationError): normalize_citation_envelope({"schema_version": version, "citation_status": status, "items": items})
    with pytest.raises(CitationError): serialize_citation_envelope([{"page_start": 10 ** 5000, "page_end": 10 ** 5000}])
def test_preparation_rejects_malformed_optional_metadata_instead_of_dropping_it():
    for document in (_document(metadata={"url": "javascript:alert(1)"}),
                     _document(retrieval_mode="hybrid\x00forged"),
                     _document(metadata={"section_path": ["Forged"]})):
        with pytest.raises(CitationError): prepare_evidence([document])
def test_evidence_and_answer_byte_budgets_fail_closed():
    duplicate = [_document("Same", 0), _document("Same", 0)]
    over_total = [_document("x" * 7000, index) for index in range(5)]
    for documents in ([_document("")], [_document("unsafe\x00text")],
                      [_document("unsafe\u202etext")], [_document("unsafe\u2028text")],
                      [_document("unsafe\u2029text")], [_document("é" * 4097)],
                      [_document(metadata={"fragment_hash": "0" * 64})], duplicate, over_total):
        with pytest.raises(CitationError):
            prepare_evidence(documents)
    first_five = [_document(str(index), index) for index in range(5)]
    assert len(prepare_evidence(first_five + [{"malformed": True}])) == 5
    evidence = prepare_evidence([_document()])
    for hostile in (type("BoolBomb", (), {"__bool__": lambda self: (_ for _ in ()).throw(RuntimeError("boom"))})(), type("LenBomb", (list,), {"__len__": lambda self: (_ for _ in ()).throw(RuntimeError("boom"))})()): pytest.raises(CitationError, validate_answer_citations, "Supported [C1].", hostile)
    for answer in ("No marker.", "é" * 8193 + " [C1]"):
        assert validate_answer_citations(answer, evidence)["citation_status"] == "invalid_citations"
