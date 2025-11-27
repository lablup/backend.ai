from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

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
        redis_container,  # noqa: F811
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

    @pytest.fixture
    def sample_huggingface_registry_data(self) -> HuggingFaceRegistryData:
        """Sample HuggingFace registry data for testing."""
        return HuggingFaceRegistryData(
            id=uuid.uuid4(),
            name="test-hf-registry",
            url="https://huggingface.co",
            token="test-token-123",
        )

    @pytest.fixture
    def sample_reservoir_registry_data(self) -> ReservoirRegistryData:
        """Sample Reservoir registry data for testing."""
        return ReservoirRegistryData(
            id=uuid.uuid4(),
            name="test-reservoir-registry",
            endpoint="https://reservoir.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            api_version="v1",
        )

    @pytest.mark.asyncio
    async def test_set_and_get_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryData,
    ) -> None:
        """Test caching and retrieving HuggingFace registry data."""
        # Set registry data
        await valkey_artifact_registry_client.set_huggingface_registry(
            sample_huggingface_registry_data.name, sample_huggingface_registry_data
        )

        # Get registry data
        result = await valkey_artifact_registry_client.get_huggingface_registry(
            sample_huggingface_registry_data.name
        )

        assert result is not None
        assert result.id == sample_huggingface_registry_data.id
        assert result.name == sample_huggingface_registry_data.name
        assert result.url == sample_huggingface_registry_data.url
        assert result.token == sample_huggingface_registry_data.token

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
        sample_huggingface_registry_data: HuggingFaceRegistryData,
    ) -> None:
        """Test deleting HuggingFace registry cache."""
        # Set registry data
        await valkey_artifact_registry_client.set_huggingface_registry(
            sample_huggingface_registry_data.name, sample_huggingface_registry_data
        )

        # Delete registry data
        deleted = await valkey_artifact_registry_client.delete_huggingface_registry(
            sample_huggingface_registry_data.name
        )
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_registry_client.get_huggingface_registry(
            sample_huggingface_registry_data.name
        )
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
        sample_reservoir_registry_data: ReservoirRegistryData,
    ) -> None:
        """Test caching and retrieving Reservoir registry data."""
        # Set registry data
        await valkey_artifact_registry_client.set_reservoir_registry(
            sample_reservoir_registry_data.name, sample_reservoir_registry_data
        )

        # Get registry data
        result = await valkey_artifact_registry_client.get_reservoir_registry(
            sample_reservoir_registry_data.name
        )

        assert result is not None
        assert result.id == sample_reservoir_registry_data.id
        assert result.name == sample_reservoir_registry_data.name
        assert result.endpoint == sample_reservoir_registry_data.endpoint
        assert result.access_key == sample_reservoir_registry_data.access_key
        assert result.secret_key == sample_reservoir_registry_data.secret_key
        assert result.api_version == sample_reservoir_registry_data.api_version

    @pytest.mark.asyncio
    async def test_cache_expiration_handling(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryData,
    ) -> None:
        """Test that cache entries expire after the specified TTL."""
        # Set with 1 second expiration
        await valkey_artifact_registry_client.set_huggingface_registry(
            sample_huggingface_registry_data.name, sample_huggingface_registry_data, expiration=1
        )

        # Verify data was stored
        result = await valkey_artifact_registry_client.get_huggingface_registry(
            sample_huggingface_registry_data.name
        )
        assert result is not None
        assert result.name == sample_huggingface_registry_data.name

        # Wait for expiration (1 second + small buffer for safety)
        await asyncio.sleep(1.2)

        # Verify data has expired
        result_after_expiration = await valkey_artifact_registry_client.get_huggingface_registry(
            sample_huggingface_registry_data.name
        )
        assert result_after_expiration is None

    @pytest.mark.asyncio
    async def test_multiple_registries_isolation(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryData,
        sample_reservoir_registry_data: ReservoirRegistryData,
    ) -> None:
        """Test that different registry types are isolated from each other."""
        # Set both types with different names
        await valkey_artifact_registry_client.set_huggingface_registry(
            sample_huggingface_registry_data.name, sample_huggingface_registry_data
        )
        await valkey_artifact_registry_client.set_reservoir_registry(
            sample_reservoir_registry_data.name, sample_reservoir_registry_data
        )

        # Verify both are stored separately
        hf_result = await valkey_artifact_registry_client.get_huggingface_registry(
            sample_huggingface_registry_data.name
        )
        reservoir_result = await valkey_artifact_registry_client.get_reservoir_registry(
            sample_reservoir_registry_data.name
        )

        assert hf_result is not None
        assert hf_result.name == sample_huggingface_registry_data.name
        assert reservoir_result is not None
        assert reservoir_result.name == sample_reservoir_registry_data.name
