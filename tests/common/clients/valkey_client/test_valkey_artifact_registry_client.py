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

    @pytest.fixture
    async def stateful_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryStatefulData,
    ) -> HuggingFaceRegistryStatefulData:
        """HuggingFace registry data that is already cached."""
        await valkey_artifact_registry_client.set_registry(
            sample_huggingface_registry_data.id, sample_huggingface_registry_data.to_dict()
        )
        return sample_huggingface_registry_data

    @pytest.fixture
    async def stateful_reservoir_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_reservoir_registry_data: ReservoirRegistryStatefulData,
    ) -> ReservoirRegistryStatefulData:
        """Reservoir registry data that is already cached."""
        await valkey_artifact_registry_client.set_registry(
            sample_reservoir_registry_data.id, sample_reservoir_registry_data.to_dict()
        )
        return sample_reservoir_registry_data

    @pytest.mark.asyncio
    async def test_set_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_huggingface_registry_data: HuggingFaceRegistryStatefulData,
    ) -> None:
        """Test caching HuggingFace registry data."""
        await valkey_artifact_registry_client.set_registry(
            sample_huggingface_registry_data.id, sample_huggingface_registry_data.to_dict()
        )

        # Verify set operation worked correctly
        result_dict = await valkey_artifact_registry_client.get_registry(
            sample_huggingface_registry_data.id
        )
        assert result_dict is not None
        result = HuggingFaceRegistryStatefulData.from_dict(result_dict)
        assert result == sample_huggingface_registry_data

    @pytest.mark.asyncio
    async def test_get_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        stateful_huggingface_registry: HuggingFaceRegistryStatefulData,
    ) -> None:
        """Test retrieving HuggingFace registry data."""
        result_dict = await valkey_artifact_registry_client.get_registry(
            stateful_huggingface_registry.id
        )

        assert result_dict is not None
        result = HuggingFaceRegistryStatefulData.from_dict(result_dict)
        assert result == stateful_huggingface_registry

    @pytest.mark.asyncio
    async def test_get_nonexistent_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
    ) -> None:
        """Test retrieving nonexistent HuggingFace registry data."""
        registry_id = uuid.uuid4()

        result = await valkey_artifact_registry_client.get_registry(registry_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_huggingface_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        stateful_huggingface_registry: HuggingFaceRegistryStatefulData,
    ) -> None:
        """Test deleting HuggingFace registry cache."""
        deleted = await valkey_artifact_registry_client.delete_registry(
            stateful_huggingface_registry.id
        )
        assert deleted is True

        # Verify deletion
        result = await valkey_artifact_registry_client.get_registry(
            stateful_huggingface_registry.id
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
    async def test_set_reservoir_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        sample_reservoir_registry_data: ReservoirRegistryStatefulData,
    ) -> None:
        """Test caching Reservoir registry data."""
        await valkey_artifact_registry_client.set_registry(
            sample_reservoir_registry_data.id, sample_reservoir_registry_data.to_dict()
        )

        # Verify set operation worked correctly
        result_dict = await valkey_artifact_registry_client.get_registry(
            sample_reservoir_registry_data.id
        )
        assert result_dict is not None
        result = ReservoirRegistryStatefulData.from_dict(result_dict)
        assert result == sample_reservoir_registry_data

    @pytest.mark.asyncio
    async def test_get_reservoir_registry(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        stateful_reservoir_registry: ReservoirRegistryStatefulData,
    ) -> None:
        """Test retrieving Reservoir registry data."""
        result_dict = await valkey_artifact_registry_client.get_registry(
            stateful_reservoir_registry.id
        )

        assert result_dict is not None
        result = ReservoirRegistryStatefulData.from_dict(result_dict)
        assert result == stateful_reservoir_registry

    @pytest.mark.asyncio
    async def test_multiple_registries_isolation(
        self,
        valkey_artifact_registry_client: ValkeyArtifactRegistryClient,
        stateful_huggingface_registry: HuggingFaceRegistryStatefulData,
        stateful_reservoir_registry: ReservoirRegistryStatefulData,
    ) -> None:
        """Test that different registry types are isolated from each other."""
        # Verify both are stored separately
        hf_result_dict = await valkey_artifact_registry_client.get_registry(
            stateful_huggingface_registry.id
        )
        reservoir_result_dict = await valkey_artifact_registry_client.get_registry(
            stateful_reservoir_registry.id
        )

        assert hf_result_dict is not None
        hf_result = HuggingFaceRegistryStatefulData.from_dict(hf_result_dict)
        assert hf_result == stateful_huggingface_registry

        assert reservoir_result_dict is not None
        reservoir_result = ReservoirRegistryStatefulData.from_dict(reservoir_result_dict)
        assert reservoir_result == stateful_reservoir_registry
