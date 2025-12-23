from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.bgtask.tasks.rescan_gpu_alloc_maps import (
    RescanGPUAllocMapsHandler,
    RescanGPUAllocMapsManifest,
)
from ai.backend.manager.bgtask.types import ManagerBgtaskName


class TestRescanGPUAllocMapsHandler:
    """Tests for RescanGPUAllocMapsHandler and RescanGPUAllocMapsManifest."""

    @pytest.fixture
    def sample_agent_id(self) -> AgentId:
        """Sample agent ID for testing."""
        return AgentId("i-test-agent-123")

    @pytest.fixture
    def sample_agent_data(self, sample_agent_id: AgentId) -> MagicMock:
        """Sample agent data returned by repository."""
        agent_data = MagicMock()
        agent_data.id = sample_agent_id
        return agent_data

    @pytest.fixture
    def sample_alloc_map(self) -> dict[str, Any]:
        """Sample GPU allocation map returned by scan_gpu_alloc_map."""
        return {
            "GPU-00000000-0000-0000-0000-000000000001": 0.5,
            "GPU-00000000-0000-0000-0000-000000000002": 1.0,
        }

    @pytest.fixture
    def mock_agent_repository(self, sample_agent_data: MagicMock) -> MagicMock:
        """Mock AgentRepository."""
        repository = MagicMock()
        repository.get_by_id = AsyncMock(return_value=sample_agent_data)
        repository.update_gpu_alloc_map = AsyncMock()
        return repository

    @pytest.fixture
    def mock_agent_client(self, sample_alloc_map: dict[str, Any]) -> MagicMock:
        """Mock AgentClient."""
        client = MagicMock()
        client.scan_gpu_alloc_map = AsyncMock(return_value=sample_alloc_map)
        return client

    @pytest.fixture
    def mock_agent_pool(self, mock_agent_client: MagicMock) -> MagicMock:
        """Mock AgentPool."""
        pool = MagicMock()
        pool.get_agent_client = MagicMock(return_value=mock_agent_client)
        return pool

    @pytest.fixture
    def handler(
        self,
        mock_agent_repository: MagicMock,
        mock_agent_pool: MagicMock,
    ) -> RescanGPUAllocMapsHandler:
        """Create handler instance with mocked dependencies."""
        return RescanGPUAllocMapsHandler(
            agent_repository=mock_agent_repository,
            agent_pool=mock_agent_pool,
        )

    def test_manifest_creation(self, sample_agent_id: AgentId) -> None:
        """Test manifest can be created with AgentId."""
        manifest = RescanGPUAllocMapsManifest(agent_id=sample_agent_id)
        assert manifest.agent_id == sample_agent_id

    def test_manifest_serialization(self, sample_agent_id: AgentId) -> None:
        """Test manifest can be serialized and deserialized."""
        manifest = RescanGPUAllocMapsManifest(agent_id=sample_agent_id)

        # Serialize to dict
        data = manifest.model_dump(mode="json")
        assert data["agent_id"] == str(sample_agent_id)

        # Deserialize back
        restored = RescanGPUAllocMapsManifest.model_validate(data)
        assert restored.agent_id == sample_agent_id

    def test_handler_name(self) -> None:
        """Test handler returns correct name."""
        assert RescanGPUAllocMapsHandler.name() == ManagerBgtaskName.RESCAN_GPU_ALLOC_MAPS

    def test_handler_manifest_type(self) -> None:
        """Test handler returns correct manifest type."""
        assert RescanGPUAllocMapsHandler.manifest_type() == RescanGPUAllocMapsManifest

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        handler: RescanGPUAllocMapsHandler,
        mock_agent_repository: MagicMock,
        mock_agent_pool: MagicMock,
        mock_agent_client: MagicMock,
        sample_agent_id: AgentId,
        sample_agent_data: MagicMock,
        sample_alloc_map: dict[str, Any],
    ) -> None:
        """Test successful execution scans GPU alloc map and stores in cache."""
        manifest = RescanGPUAllocMapsManifest(agent_id=sample_agent_id)

        # Execute handler (returns None)
        await handler.execute(manifest)

        # Verify repository.get_by_id was called
        mock_agent_repository.get_by_id.assert_called_once_with(sample_agent_id)

        # Verify agent_pool.get_agent_client was called
        mock_agent_pool.get_agent_client.assert_called_once_with(sample_agent_data.id)

        # Verify agent_client.scan_gpu_alloc_map was called
        mock_agent_client.scan_gpu_alloc_map.assert_called_once()

        # Verify repository.update_gpu_alloc_map was called with correct parameters
        mock_agent_repository.update_gpu_alloc_map.assert_called_once_with(
            sample_agent_id,
            sample_alloc_map,
        )

    @pytest.mark.asyncio
    async def test_execute_scan_failure(
        self,
        handler: RescanGPUAllocMapsHandler,
        mock_agent_repository: MagicMock,
        mock_agent_client: MagicMock,
        sample_agent_id: AgentId,
    ) -> None:
        """Test execution re-raises exception when scan_gpu_alloc_map fails."""
        manifest = RescanGPUAllocMapsManifest(agent_id=sample_agent_id)

        # Mock scan_gpu_alloc_map to raise exception
        expected_error = RuntimeError("Failed to scan GPU allocation map")
        mock_agent_client.scan_gpu_alloc_map.side_effect = expected_error

        # Execute handler should re-raise the exception
        with pytest.raises(RuntimeError) as exc_info:
            await handler.execute(manifest)

        assert exc_info.value == expected_error

        # Verify repository.get_by_id was called
        mock_agent_repository.get_by_id.assert_called_once_with(sample_agent_id)

        # Verify agent_client.scan_gpu_alloc_map was called
        mock_agent_client.scan_gpu_alloc_map.assert_called_once()

        # Verify update_gpu_alloc_map was NOT called (failed before reaching that point)
        mock_agent_repository.update_gpu_alloc_map.assert_not_called()
