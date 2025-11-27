from __future__ import annotations

import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact_storages.client import (
    ValkeyArtifactStorageClient,
)
from ai.backend.common.data.object_storage.types import ObjectStorageData
from ai.backend.common.data.vfs_storage.types import VFSStorageData
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
            await client.flush_database()
            await client.close()

    @pytest.mark.asyncio
    async def test_set_and_get_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test caching and retrieving object storage data."""
        storage_uuid = uuid.uuid4()
        storage_name = "test-object-storage"
        storage_data = ObjectStorageData(
            id=storage_uuid,
            name=storage_name,
            host="s3.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            endpoint="https://s3.example.com",
            region="us-west-2",
        )

        # Set storage data
        await valkey_artifact_storage_client.set_object_storage(storage_name, storage_data)

        # Get storage data
        result = await valkey_artifact_storage_client.get_object_storage(storage_name)

        assert result is not None
        assert result.id == storage_uuid
        assert result.name == storage_name
        assert result.host == "s3.example.com"
        assert result.access_key == "test-access-key"
        assert result.secret_key == "test-secret-key"
        assert result.endpoint == "https://s3.example.com"
        assert result.region == "us-west-2"

    @pytest.mark.asyncio
    async def test_get_nonexistent_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test retrieving nonexistent object storage data."""
        storage_name = "nonexistent-storage"

        result = await valkey_artifact_storage_client.get_object_storage(storage_name)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test deleting object storage cache."""
        storage_uuid = uuid.uuid4()
        storage_name = "test-object-storage"
        storage_data = ObjectStorageData(
            id=storage_uuid,
            name=storage_name,
            host="s3.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            endpoint="https://s3.example.com",
            region="us-west-2",
        )

        # Set storage data
        await valkey_artifact_storage_client.set_object_storage(storage_name, storage_data)

        # Delete storage data
        deleted = await valkey_artifact_storage_client.delete_object_storage(storage_name)
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_storage_client.get_object_storage(storage_name)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_object_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test deleting nonexistent object storage cache."""
        storage_name = "nonexistent-storage"

        deleted = await valkey_artifact_storage_client.delete_object_storage(storage_name)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_set_and_get_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test caching and retrieving VFS storage data."""
        storage_uuid = uuid.uuid4()
        storage_name = "test-vfs-storage"
        storage_data = VFSStorageData(
            id=storage_uuid,
            name=storage_name,
            host="vfs.example.com",
            base_path=Path("/mnt/vfs/storage"),
        )

        # Set storage data
        await valkey_artifact_storage_client.set_vfs_storage(storage_name, storage_data)

        # Get storage data
        result = await valkey_artifact_storage_client.get_vfs_storage(storage_name)

        assert result is not None
        assert result.id == storage_uuid
        assert result.name == storage_name
        assert result.host == "vfs.example.com"
        assert result.base_path == Path("/mnt/vfs/storage")

    @pytest.mark.asyncio
    async def test_get_nonexistent_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test retrieving nonexistent VFS storage data."""
        storage_name = "nonexistent-vfs-storage"

        result = await valkey_artifact_storage_client.get_vfs_storage(storage_name)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test deleting VFS storage cache."""
        storage_uuid = uuid.uuid4()
        storage_name = "test-vfs-storage"
        storage_data = VFSStorageData(
            id=storage_uuid,
            name=storage_name,
            host="vfs.example.com",
            base_path=Path("/mnt/vfs/storage"),
        )

        # Set storage data
        await valkey_artifact_storage_client.set_vfs_storage(storage_name, storage_data)

        # Delete storage data
        deleted = await valkey_artifact_storage_client.delete_vfs_storage(storage_name)
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_storage_client.get_vfs_storage(storage_name)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_vfs_storage(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test deleting nonexistent VFS storage cache."""
        storage_name = "nonexistent-vfs-storage"

        deleted = await valkey_artifact_storage_client.delete_vfs_storage(storage_name)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_cache_expiration_handling(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test setting cache with custom expiration."""
        storage_uuid = uuid.uuid4()
        storage_name = "test-expiring-storage"
        storage_data = ObjectStorageData(
            id=storage_uuid,
            name=storage_name,
            host="s3.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            endpoint="https://s3.example.com",
            region="us-west-2",
        )

        # Set with short expiration (1 second for testing purposes would be ideal,
        # but for this test we just verify the API accepts the parameter)
        await valkey_artifact_storage_client.set_object_storage(
            storage_name, storage_data, expiration=60
        )

        # Verify data was stored
        result = await valkey_artifact_storage_client.get_object_storage(storage_name)
        assert result is not None
        assert result.name == storage_name

    @pytest.mark.asyncio
    async def test_multiple_storage_types_isolation(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test that different storage types are isolated from each other."""
        object_uuid = uuid.uuid4()
        object_name = "object-storage"
        object_data = ObjectStorageData(
            id=object_uuid,
            name=object_name,
            host="s3.example.com",
            access_key="object-access",
            secret_key="object-secret",
            endpoint="https://s3.example.com",
            region="us-west-2",
        )

        vfs_uuid = uuid.uuid4()
        vfs_name = "vfs-storage"
        vfs_data = VFSStorageData(
            id=vfs_uuid,
            name=vfs_name,
            host="vfs.example.com",
            base_path=Path("/mnt/vfs/storage"),
        )

        # Set both types with different names
        await valkey_artifact_storage_client.set_object_storage(object_name, object_data)
        await valkey_artifact_storage_client.set_vfs_storage(vfs_name, vfs_data)

        # Verify both are stored separately
        object_result = await valkey_artifact_storage_client.get_object_storage(object_name)
        vfs_result = await valkey_artifact_storage_client.get_vfs_storage(vfs_name)

        assert object_result is not None
        assert object_result.name == object_name
        assert vfs_result is not None
        assert vfs_result.name == vfs_name

    @pytest.mark.asyncio
    async def test_same_name_different_storage_types_isolation(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test that storage types with the same name are isolated by type."""
        storage_name = "same-name-storage"
        object_uuid = uuid.uuid4()
        vfs_uuid = uuid.uuid4()

        object_data = ObjectStorageData(
            id=object_uuid,
            name=storage_name,
            host="s3.example.com",
            access_key="object-access",
            secret_key="object-secret",
            endpoint="https://s3.example.com",
            region="us-west-2",
        )

        vfs_data = VFSStorageData(
            id=vfs_uuid,
            name=storage_name,
            host="vfs.example.com",
            base_path=Path("/mnt/vfs/storage"),
        )

        # Set both types with the same name
        await valkey_artifact_storage_client.set_object_storage(storage_name, object_data)
        await valkey_artifact_storage_client.set_vfs_storage(storage_name, vfs_data)

        # Verify both are stored separately despite same name
        object_result = await valkey_artifact_storage_client.get_object_storage(storage_name)
        vfs_result = await valkey_artifact_storage_client.get_vfs_storage(storage_name)

        assert object_result is not None
        assert object_result.id == object_uuid
        assert object_result.host == "s3.example.com"

        assert vfs_result is not None
        assert vfs_result.id == vfs_uuid
        assert vfs_result.host == "vfs.example.com"

        # Delete object storage should not affect VFS storage
        deleted = await valkey_artifact_storage_client.delete_object_storage(storage_name)
        assert deleted is True

        # VFS storage should still exist
        vfs_result_after_delete = await valkey_artifact_storage_client.get_vfs_storage(storage_name)
        assert vfs_result_after_delete is not None
        assert vfs_result_after_delete.id == vfs_uuid

    @pytest.mark.asyncio
    async def test_path_serialization_deserialization(
        self,
        valkey_artifact_storage_client: ValkeyArtifactStorageClient,
    ) -> None:
        """Test that Path objects are correctly serialized and deserialized."""
        storage_uuid = uuid.uuid4()
        storage_name = "path-test-storage"
        complex_path = Path("/complex/path/with/multiple/levels")

        storage_data = VFSStorageData(
            id=storage_uuid,
            name=storage_name,
            host="vfs.example.com",
            base_path=complex_path,
        )

        # Set storage data
        await valkey_artifact_storage_client.set_vfs_storage(storage_name, storage_data)

        # Get storage data
        result = await valkey_artifact_storage_client.get_vfs_storage(storage_name)

        assert result is not None
        assert result.base_path == complex_path
        assert isinstance(result.base_path, Path)
        assert str(result.base_path) == "/complex/path/with/multiple/levels"
