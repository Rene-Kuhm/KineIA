import inspect
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.api.deps import get_database
from app.api.v1 import knowledge
from app.services.source_ingestion import InactiveSourceError, IngestionFailureError
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(knowledge.router)
    signature = inspect.signature(knowledge.ingest_document)
    auth = signature.parameters["current_user"].default.dependency
    database = object()
    app.dependency_overrides[auth] = lambda: object()
    app.dependency_overrides[get_database] = lambda: database
    service = AsyncMock(return_value={"chunks": 1})
    monkeypatch.setattr(knowledge, "ingest_trusted_file", service, raising=False)
    http = TestClient(app)
    http.database, http.service = database, service
    return http


def test_upload_requires_governance_metadata(client):
    response = client.post(
        "/knowledge/ingest", files={"file": ("guide.md", b"evidence", "text/markdown")}
    )

    assert response.status_code == 422
    missing = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"reviewer", "review_date"} <= missing


@pytest.mark.parametrize("filename", ["../../Guide.md", r"..\..\Guide.md"])
def test_upload_uses_governed_orchestration_and_cleans_temp_file(client, filename):
    response = client.post(
        "/knowledge/ingest",
        files={"file": (filename, b"evidence", "text/markdown")},
        data={
            "reviewer": "  Lic. Ana Pérez  ",
            "review_date": "2026-07-17",
            "area": "Neurología",
            "source_type": "clinical-guide",
            "evidence_level": "protocol",
            "title": "Guide",
            "university": "UBA",
            "author": "Author",
            "year": "2026",
            "source_key": "clinic/guide",
        },
    )

    session, temp_path, metadata = client.service.await_args.args
    assert response.status_code == 200 and response.json()["data"]["file"] == "Guide.md"
    assert session is client.database and not Path(temp_path).exists()
    assert (metadata["reviewer"], metadata["review_date"]) == ("Lic. Ana Pérez", "2026-07-17")
    assert (metadata["area"], metadata["source_key"]) == ("Neurología", "clinic/guide")
    optional = [metadata[key] for key in ("source_type", "university", "author", "year")]
    assert optional == ["clinical-guide", "UBA", "Author", 2026]


@pytest.mark.parametrize(
    "data",
    [
        {"reviewer": "   ", "review_date": "2026-07-17"},
        {"reviewer": "Lic. Ana Pérez", "review_date": "not-a-date"},
    ],
)
def test_upload_rejects_invalid_governance_metadata(client, data):
    response = client.post(
        "/knowledge/ingest",
        files={"file": ("guide.md", b"evidence", "text/markdown")},
        data=data,
    )

    assert response.status_code == 422
    client.service.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (InactiveSourceError("password=inactive-secret"), 409),
        (ValueError("password=metadata-secret"), 400),
        (IngestionFailureError("qdrant_upsert"), 500),
        (RuntimeError("password=service-secret"), 500),
    ],
)
def test_upload_sanitizes_service_failures_and_cleans_temp_file(client, error, expected_status):
    paths = []

    async def fail(_session, path, _metadata):
        paths.append(path)
        raise error

    client.service.side_effect = fail
    response = client.post(
        "/knowledge/ingest",
        files={"file": ("guide.md", b"evidence", "text/markdown")},
        data={"reviewer": "Lic. Ana Pérez", "review_date": "2026-07-17"},
    )

    assert response.status_code == expected_status and "secret" not in response.text
    assert paths and not Path(paths[0]).exists()


def test_openapi_requires_file_and_governance_fields(client):
    schema = client.app.openapi()
    body = schema["paths"]["/knowledge/ingest"]["post"]["requestBody"]
    upload = body["content"]["multipart/form-data"]["schema"]
    upload = schema["components"]["schemas"][upload["$ref"].rsplit("/", 1)[-1]]

    assert {"file", "reviewer", "review_date"} <= set(upload["required"])
