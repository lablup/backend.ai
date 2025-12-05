from __future__ import annotations

import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact_storages.client import (
    ValkeyArtifactStorageClient,
)
from ai.backend.common.data.storage.types import (
    ObjectStorageStatefulData,
    VFSStorageStatefulData,
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
    def sample_object_storage_data(self) -> ObjectStorageStatefulData:
        """Sample object storage data for testing"""
        return ObjectStorageStatefulData(
            id=uuid.uuid4(),
            name="test-object-storage",
            host="s3.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            endpoint="https://s3.example.com",
            region="us-west-2",
        )

    @pytest.fixture
    def sample_vfs_storage_data(self) -> VFSStorageStatefulData:
        """Sample VFS storage data for testing"""
        return VFSStorageStatefulData(
            id=uuid.uuid4(),
            name="test-vfs-storage",
            host="vfs.example.com",
            base_path=Path("/mnt/vfs/storage"),
        )

    @pytest.fixture
    async def stateful_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        sample_object_storage_data: ObjectStorageStatefulData,
    ) -> ObjectStorageStatefulData:
        """Object storage data that is already cached."""
        await valkey_artifact_storage_client.set_storage(
            sample_object_storage_data.id, sample_object_storage_data.to_dict()
        )
        return sample_object_storage_data

    @pytest.fixture
    async def stateful_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        sample_vfs_storage_data: VFSStorageStatefulData,
    ) -> VFSStorageStatefulData:
        """VFS storage data that is already cached."""
        await valkey_artifact_storage_client.set_storage(
            sample_vfs_storage_data.id, sample_vfs_storage_data.to_dict()
        )
        return sample_vfs_storage_data

    @pytest.mark.asyncio
    async def test_set_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        sample_object_storage_data: ObjectStorageStatefulData,
    ) -> None:
        """Test caching object storage data."""
        await valkey_artifact_storage_client.set_storage(
            sample_object_storage_data.id, sample_object_storage_data.to_dict()
        )

        # Verify set operation worked correctly
        result_dict = await valkey_artifact_storage_client.get_storage(
            sample_object_storage_data.id
        )
        assert result_dict is not None
        result = ObjectStorageStatefulData.from_dict(result_dict)
        assert result == sample_object_storage_data

    @pytest.mark.asyncio
    async def test_get_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        stateful_object_storage: ObjectStorageStatefulData,
    ) -> None:
        """Test retrieving object storage data."""
        result_dict = await valkey_artifact_storage_client.get_storage(stateful_object_storage.id)

        assert result_dict is not None
        result = ObjectStorageStatefulData.from_dict(result_dict)
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
        stateful_object_storage: ObjectStorageStatefulData,
    ) -> None:
        """Test deleting object storage cache."""
        deleted = await valkey_artifact_storage_client.delete_storage(stateful_object_storage.id)
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_storage_client.get_storage(stateful_object_storage.id)
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
        sample_vfs_storage_data: VFSStorageStatefulData,
    ) -> None:
        """Test caching VFS storage data."""
        await valkey_artifact_storage_client.set_storage(
            sample_vfs_storage_data.id, sample_vfs_storage_data.to_dict()
        )

        # Verify set operation worked correctly
        result_dict = await valkey_artifact_storage_client.get_storage(sample_vfs_storage_data.id)
        assert result_dict is not None
        result = VFSStorageStatefulData.from_dict(result_dict)
        assert result == sample_vfs_storage_data

    @pytest.mark.asyncio
    async def test_get_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
        stateful_vfs_storage: VFSStorageStatefulData,
    ) -> None:
        """Test retrieving VFS storage data."""
        result_dict = await valkey_artifact_storage_client.get_storage(stateful_vfs_storage.id)

        assert result_dict is not None
        result = VFSStorageStatefulData.from_dict(result_dict)
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
        stateful_vfs_storage: VFSStorageStatefulData,
    ) -> None:
        """Test deleting VFS storage cache."""
        deleted = await valkey_artifact_storage_client.delete_storage(stateful_vfs_storage.id)
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_storage_client.get_storage(stateful_vfs_storage.id)
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
        stateful_object_storage: ObjectStorageStatefulData,
        stateful_vfs_storage: VFSStorageStatefulData,
    ) -> None:
        """Test that different storage types are isolated from each other."""
        # Verify both are stored separately
        object_result_dict = await valkey_artifact_storage_client.get_storage(
            stateful_object_storage.id
        )
        vfs_result_dict = await valkey_artifact_storage_client.get_storage(stateful_vfs_storage.id)

        assert object_result_dict is not None
        object_result = ObjectStorageStatefulData.from_dict(object_result_dict)
        assert object_result == stateful_object_storage

        assert vfs_result_dict is not None
        vfs_result = VFSStorageStatefulData.from_dict(vfs_result_dict)
        assert vfs_result == stateful_vfs_storage
