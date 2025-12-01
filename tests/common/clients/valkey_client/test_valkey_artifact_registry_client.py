from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.valkey_artifact_registries.client import (
    ValkeyArtifactRegistryClient,
)
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.artifact_registry.types import (
    HuggingFaceRegistryStatefulData,
    ReservoirRegistryStatefulData,
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
    def sample_huggingface_registry_data(self) -> HuggingFaceRegistryStatefulData:
        """Sample HuggingFace registry data for testing."""
        return HuggingFaceRegistryStatefulData(
            id=uuid.uuid4(),
            registry_id=uuid.uuid4(),
            name="test-hf-registry",
            type=ArtifactRegistryType.HUGGINGFACE,
            url="https://huggingface.co",
            token="test-token-123",
        )

    @pytest.fixture
    def sample_reservoir_registry_data(self) -> ReservoirRegistryStatefulData:
        """Sample Reservoir registry data for testing."""
        return ReservoirRegistryStatefulData(
            id=uuid.uuid4(),
            registry_id=uuid.uuid4(),
            name="test-reservoir-registry",
            type=ArtifactRegistryType.RESERVOIR,
            endpoint="https://reservoir.example.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            api_version="v1",
        )

    @pytest.mark.asyncio
    async def test_set_and_get_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryStatefulData,
    ) -> None:
        """Test caching and retrieving HuggingFace registry data."""
        # Set registry data
        await valkey_artifact_registry_client.set_registry(
            sample_huggingface_registry_data.id, sample_huggingface_registry_data
        )

        # Get registry data
        result = await valkey_artifact_registry_client.get_registry(
            sample_huggingface_registry_data.id, HuggingFaceRegistryStatefulData
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
        registry_id = uuid.uuid4()

        result = await valkey_artifact_registry_client.get_registry(
            registry_id, HuggingFaceRegistryStatefulData
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryStatefulData,
    ) -> None:
        """Test deleting HuggingFace registry cache."""
        # Set registry data
        await valkey_artifact_registry_client.set_registry(
            sample_huggingface_registry_data.id, sample_huggingface_registry_data
        )

        # Delete registry data
        deleted = await valkey_artifact_registry_client.delete_registry(
            sample_huggingface_registry_data.id
        )
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_registry_client.get_registry(
            sample_huggingface_registry_data.id, HuggingFaceRegistryStatefulData
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test deleting nonexistent HuggingFace registry cache."""
        registry_id = uuid.uuid4()

        deleted = await valkey_artifact_registry_client.delete_registry(registry_id)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_set_and_get_reservoir_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_reservoir_registry_data: ReservoirRegistryStatefulData,
    ) -> None:
        """Test caching and retrieving Reservoir registry data."""
        # Set registry data
        await valkey_artifact_registry_client.set_registry(
            sample_reservoir_registry_data.id, sample_reservoir_registry_data
        )

        # Get registry data
        result = await valkey_artifact_registry_client.get_registry(
            sample_reservoir_registry_data.id, ReservoirRegistryStatefulData
        )

        assert result is not None
        assert result.id == sample_reservoir_registry_data.id
        assert result.name == sample_reservoir_registry_data.name
        assert result.endpoint == sample_reservoir_registry_data.endpoint
        assert result.access_key == sample_reservoir_registry_data.access_key
        assert result.secret_key == sample_reservoir_registry_data.secret_key
        assert result.api_version == sample_reservoir_registry_data.api_version

    @pytest.mark.asyncio
    async def test_multiple_registries_isolation(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryStatefulData,
        sample_reservoir_registry_data: ReservoirRegistryStatefulData,
    ) -> None:
        """Test that different registry types are isolated from each other."""
        # Set both types with different IDs
        await valkey_artifact_registry_client.set_registry(
            sample_huggingface_registry_data.id, sample_huggingface_registry_data
        )
        await valkey_artifact_registry_client.set_registry(
            sample_reservoir_registry_data.id, sample_reservoir_registry_data
        )

        # Verify both are stored separately
        hf_result = await valkey_artifact_registry_client.get_registry(
            sample_huggingface_registry_data.id, HuggingFaceRegistryStatefulData
        )
        reservoir_result = await valkey_artifact_registry_client.get_registry(
            sample_reservoir_registry_data.id, ReservoirRegistryStatefulData
        )

        assert hf_result is not None
        assert hf_result.name == sample_huggingface_registry_data.name
        assert reservoir_result is not None
        assert reservoir_result.name == sample_reservoir_registry_data.name
