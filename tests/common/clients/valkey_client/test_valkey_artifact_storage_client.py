from __future__ import annotations

import uuid
from typing import Any, AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact_storages.client import (
    ValkeyArtifactStorageClient,
)
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


class TestValkeyArtifactStorageClient:
    """Test cases for ValkeyArtifactStorageClient"""

    @pytest.fixture
    async def valkey_artifact_storage_client(
        self,
        redis_container,  # noqa: F811
    ) -> AsyncGenerator[ValkeyArtifactStorageClient, None]:
        """Valkey client that auto-cleans cache after each test"""
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )
        client = await ValkeyArtifactStorageClient.create(
            valkey_target,
            human_readable_name="test.artifact_storage",
            db_id=0,
        )
        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    def sample_object_storage_data(self) -> dict[str, Any]:
        """Sample object storage data for testing"""
        return {
            "id": str(uuid.uuid4()),
            "name": "test-object-storage",
            "host": "s3.example.com",
            "access_key": "test-access-key",
            "secret_key": "test-secret-key",
            "endpoint": "https://s3.example.com",
            "region": "us-west-2",
        }

    @pytest.fixture
    def sample_vfs_storage_data(self) -> dict[str, Any]:
        """Sample VFS storage data for testing"""
        return {
            "id": str(uuid.uuid4()),
            "name": "test-vfs-storage",
            "host": "vfs.example.com",
            "base_path": "/mnt/vfs/storage",
        }

    @pytest.fixture
    async def stateful_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        sample_object_storage_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Object storage data that is already cached."""
        storage_id = uuid.UUID(sample_object_storage_data["id"])
        await valkey_artifact_storage_client.set_storage(storage_id, sample_object_storage_data)
        return sample_object_storage_data

    @pytest.fixture
    async def stateful_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        sample_vfs_storage_data: dict[str, Any],
    ) -> dict[str, Any]:
        """VFS storage data that is already cached."""
        storage_id = uuid.UUID(sample_vfs_storage_data["id"])
        await valkey_artifact_storage_client.set_storage(storage_id, sample_vfs_storage_data)
        return sample_vfs_storage_data

    @pytest.mark.asyncio
    async def test_set_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        sample_object_storage_data: dict[str, Any],
    ) -> None:
        """Test caching object storage data."""
        storage_id = uuid.UUID(sample_object_storage_data["id"])

        await valkey_artifact_storage_client.set_storage(storage_id, sample_object_storage_data)

        # Verify set operation worked correctly
        result = await valkey_artifact_storage_client.get_storage(storage_id)
        assert result is not None
        assert result == sample_object_storage_data

    @pytest.mark.asyncio
    async def test_get_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        stateful_object_storage: dict[str, Any],
    ) -> None:
        """Test retrieving object storage data."""
        storage_id = uuid.UUID(stateful_object_storage["id"])

        result = await valkey_artifact_storage_client.get_storage(storage_id)

        assert result is not None
        assert result == stateful_object_storage

    @pytest.mark.asyncio
    async def test_get_nonexistent_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test retrieving nonexistent object storage data."""
        storage_id = uuid.uuid4()

        result = await valkey_artifact_storage_client.get_storage(storage_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        stateful_object_storage: dict[str, Any],
    ) -> None:
        """Test deleting object storage cache."""
        storage_id = uuid.UUID(stateful_object_storage["id"])

        deleted = await valkey_artifact_storage_client.delete_storage(storage_id)
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_storage_client.get_storage(storage_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test deleting nonexistent object storage cache."""
        storage_id = uuid.uuid4()

        deleted = await valkey_artifact_storage_client.delete_storage(storage_id)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_set_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        sample_vfs_storage_data: dict[str, Any],
    ) -> None:
        """Test caching VFS storage data."""
        storage_id = uuid.UUID(sample_vfs_storage_data["id"])

        await valkey_artifact_storage_client.set_storage(storage_id, sample_vfs_storage_data)

        # Verify set operation worked correctly
        result = await valkey_artifact_storage_client.get_storage(storage_id)
        assert result is not None
        assert result == sample_vfs_storage_data

    @pytest.mark.asyncio
    async def test_get_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        stateful_vfs_storage: dict[str, Any],
    ) -> None:
        """Test retrieving VFS storage data."""
        storage_id = uuid.UUID(stateful_vfs_storage["id"])

        result = await valkey_artifact_storage_client.get_storage(storage_id)

        assert result is not None
        assert result == stateful_vfs_storage

    @pytest.mark.asyncio
    async def test_get_nonexistent_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test retrieving nonexistent VFS storage data."""
        storage_id = uuid.uuid4()

        result = await valkey_artifact_storage_client.get_storage(storage_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        stateful_vfs_storage: dict[str, Any],
    ) -> None:
        """Test deleting VFS storage cache."""
        storage_id = uuid.UUID(stateful_vfs_storage["id"])

        deleted = await valkey_artifact_storage_client.delete_storage(storage_id)
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_storage_client.get_storage(storage_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test deleting nonexistent VFS storage cache."""
        storage_id = uuid.uuid4()

        deleted = await valkey_artifact_storage_client.delete_storage(storage_id)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_multiple_storage_types_isolation(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        stateful_object_storage: dict[str, Any],
        stateful_vfs_storage: dict[str, Any],
    ) -> None:
        """Test that different storage types are isolated from each other."""
        # Verify both are stored separately
        object_result = await valkey_artifact_storage_client.get_storage(
            uuid.UUID(stateful_object_storage["id"])
        )
        vfs_result = await valkey_artifact_storage_client.get_storage(
            uuid.UUID(stateful_vfs_storage["id"])
        )

        assert object_result is not None
        assert object_result == stateful_object_storage

        assert vfs_result is not None
        assert vfs_result == stateful_vfs_storage
