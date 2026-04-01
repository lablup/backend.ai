from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow

ObjectStorageFixtureData = dict[str, Any]
ObjectStorageFactory = Callable[..., Coroutine[Any, Any, ObjectStorageFixtureData]]
StorageNamespaceFixtureData = dict[str, Any]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, StorageNamespaceFixtureData]]


@pytest.fixture()
async def object_storage_factory(
    db_engine: SAEngine,
) -> AsyncIterator[ObjectStorageFactory]:
    """Factory that inserts ObjectStorageRow directly into DB for integration tests."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> ObjectStorageFixtureData:
        unique = secrets.token_hex(4)
        storage_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": storage_id,
            "name": f"test-storage-{unique}",
            "host": "s3.example.com",
            "access_key": f"AK-{unique}",
            "secret_key": f"SK-{unique}",
            "endpoint": f"https://s3.example.com/{unique}",
            "region": "us-east-1",
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(ObjectStorageRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for sid in reversed(created_ids):
            await conn.execute(
                sa.delete(StorageNamespaceRow.__table__).where(
                    StorageNamespaceRow.__table__.c.storage_id == sid
                )
            )
            await conn.execute(
                sa.delete(ObjectStorageRow.__table__).where(ObjectStorageRow.__table__.c.id == sid)
            )


@pytest.fixture()
async def storage_namespace_factory(
    db_engine: SAEngine,
) -> AsyncIterator[StorageNamespaceFactory]:
    """Factory that inserts StorageNamespaceRow directly into DB for integration tests."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> StorageNamespaceFixtureData:
        unique = secrets.token_hex(4)
        ns_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": ns_id,
            "namespace": f"test-bucket-{unique}",
        }
        defaults.update(overrides)
        if "storage_id" not in defaults:
            raise ValueError("storage_id is required for storage_namespace_factory")
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(StorageNamespaceRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for nid in reversed(created_ids):
            await conn.execute(
                sa.delete(StorageNamespaceRow.__table__).where(
                    StorageNamespaceRow.__table__.c.id == nid
                )
            )
