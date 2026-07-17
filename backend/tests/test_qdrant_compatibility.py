from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qdrant_client.models import Distance, VectorParams


@pytest.fixture
def subject(monkeypatch):
    from app.db import qdrant as module

    client = MagicMock()
    monkeypatch.setattr(module, "qdrant_client", client)
    return module, client


def existing(client, name, vectors):
    client.get_collections.return_value.collections = [SimpleNamespace(name=name)]
    client.get_collection.return_value.config.params.vectors = vectors


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "vectors",
    [
        VectorParams(size=384, distance=Distance.COSINE),
        VectorParams(size=1024, distance=Distance.DOT),
        {"dense": VectorParams(size=1024, distance=Distance.COSINE)},
    ],
)
async def test_incompatible_existing_collection_fails_without_mutation(subject, vectors):
    module, client = subject
    existing(client, module.settings.qdrant_collection, vectors)

    with pytest.raises(RuntimeError, match="incompatible"):
        await module.init_qdrant_collection()

    client.create_collection.assert_not_called()
    client.delete_collection.assert_not_called()


@pytest.mark.asyncio
async def test_compatible_existing_collection_is_left_untouched(subject):
    module, client = subject
    existing(
        client,
        module.settings.qdrant_collection,
        VectorParams(size=1024, distance=Distance.COSINE),
    )

    await module.init_qdrant_collection()

    client.create_collection.assert_not_called()
    client.delete_collection.assert_not_called()


@pytest.mark.asyncio
async def test_missing_collection_is_created_with_legacy_dense_schema(subject):
    module, client = subject
    client.get_collections.return_value.collections = []

    await module.init_qdrant_collection()

    config = client.create_collection.call_args.kwargs["vectors_config"]
    assert (config.size, config.distance) == (1024, Distance.COSINE)
    client.delete_collection.assert_not_called()
