from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.data.artifact_registry.types import (
    HuggingFaceRegistryData,
    ReservoirRegistryData,
)
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


class TestValkeyArtifactRegistryClient:
    """Test cases for ValkeyArtifactRegistryClient"""

    @pytest.fixture
    async def valkey_artifact_registry_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ValkeyArtifactRegistryClient, None]:
        """Valkey client that auto-cleans cache after each test"""
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )
        client = await ValkeyArtifactRegistryClient.create(
            valkey_target,
            human_readable_name="test.artifact_registry",
            db_id=0,
        )
        try:
            yield client
        finally:
            await client.flush_database()
            await client.close()

    @pytest.mark.asyncio
    async def test_set_and_get_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test caching and retrieving HuggingFace registry data."""
        registry_uuid = uuid.uuid4()
        registry_name = "test-hf-registry"
        registry_data = HuggingFaceRegistryData(
            id=registry_uuid,
            name=registry_name,
            url="https://huggingface.co",
            token="test-token-123",
        )

        # Set registry data
        await valkey_artifact_registry_client.set_huggingface_registry(registry_name, registry_data)

        # Get registry data
        result = await valkey_artifact_registry_client.get_huggingface_registry(registry_name)

        assert result is not None
        assert result.id == registry_uuid
        assert result.name == registry_name
        assert result.url == "https://huggingface.co"
        assert result.token == "test-token-123"

    @pytest.mark.asyncio
    async def test_get_nonexistent_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test retrieving nonexistent HuggingFace registry data."""
        registry_name = "nonexistent-registry"

        result = await valkey_artifact_registry_client.get_huggingface_registry(registry_name)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test deleting HuggingFace registry cache."""
        registry_uuid = uuid.uuid4()
        registry_name = "test-hf-registry"
        registry_data = HuggingFaceRegistryData(
            id=registry_uuid,
            name=registry_name,
            url="https://huggingface.co",
            token="test-token-123",
        )

        # Set registry data
        await valkey_artifact_registry_client.set_huggingface_registry(registry_name, registry_data)

        # Delete registry data
        deleted = await valkey_artifact_registry_client.delete_huggingface_registry(registry_name)
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_registry_client.get_huggingface_registry(registry_name)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test deleting nonexistent HuggingFace registry cache."""
        registry_name = "nonexistent-registry"

        deleted = await valkey_artifact_registry_client.delete_huggingface_registry(registry_name)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_set_and_get_reservoir_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test caching and retrieving Reservoir registry data."""
        registry_uuid = uuid.uuid4()
        registry_name = "test-reservoir-registry"
        registry_data = ReservoirRegistryData(
            id=registry_uuid,
            name=registry_name,
            endpoint="https://reservoir.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            api_version="v1",
        )

        # Set registry data
        await valkey_artifact_registry_client.set_reservoir_registry(registry_name, registry_data)

        # Get registry data
        result = await valkey_artifact_registry_client.get_reservoir_registry(registry_name)

        assert result is not None
        assert result.id == registry_uuid
        assert result.name == registry_name
        assert result.endpoint == "https://reservoir.example.com"
        assert result.access_key == "test-access-key"
        assert result.secret_key == "test-secret-key"
        assert result.api_version == "v1"

    @pytest.mark.asyncio
    async def test_cache_expiration_handling(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test setting cache with custom expiration."""
        registry_uuid = uuid.uuid4()
        registry_name = "test-expiring-registry"
        registry_data = HuggingFaceRegistryData(
            id=registry_uuid,
            name=registry_name,
            url="https://huggingface.co",
            token="test-token-789",
        )

        # Set with short expiration (1 second for testing purposes would be ideal,
        # but for this test we just verify the API accepts the parameter)
        await valkey_artifact_registry_client.set_huggingface_registry(
            registry_name, registry_data, expiration=60
        )

        # Verify data was stored
        result = await valkey_artifact_registry_client.get_huggingface_registry(registry_name)
        assert result is not None
        assert result.name == registry_name

    @pytest.mark.asyncio
    async def test_multiple_registries_isolation(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test that different registry types are isolated from each other."""
        hf_uuid = uuid.uuid4()
        hf_name = "hf-registry"
        hf_data = HuggingFaceRegistryData(
            id=hf_uuid,
            name=hf_name,
            url="https://huggingface.co",
            token="hf-token",
        )

        reservoir_uuid = uuid.uuid4()
        reservoir_name = "reservoir-registry"
        reservoir_data = ReservoirRegistryData(
            id=reservoir_uuid,
            name=reservoir_name,
            endpoint="https://reservoir.example.com",
            access_key="reservoir-access",
            secret_key="reservoir-secret",
            api_version="v1",
        )

        # Set both types with different names
        await valkey_artifact_registry_client.set_huggingface_registry(hf_name, hf_data)
        await valkey_artifact_registry_client.set_reservoir_registry(reservoir_name, reservoir_data)

        # Verify both are stored separately
        hf_result = await valkey_artifact_registry_client.get_huggingface_registry(hf_name)
        reservoir_result = await valkey_artifact_registry_client.get_reservoir_registry(
            reservoir_name
        )

        assert hf_result is not None
        assert hf_result.name == hf_name
        assert reservoir_result is not None
        assert reservoir_result.name == reservoir_name
