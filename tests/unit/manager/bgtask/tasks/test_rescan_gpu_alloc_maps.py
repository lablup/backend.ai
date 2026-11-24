from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.agent.types import GPUDeviceAllocation
from ai.backend.common.dto.agent.response import ScanGPUDevicesResp
from ai.backend.common.types import AgentId, DeviceId
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
    def scanned_gpu_devices(self) -> list[GPUDeviceAllocation]:
        """GPU devices returned by scan_gpu_devices."""
        return [
            GPUDeviceAllocation(
                device_id=DeviceId("GPU-00000000-0000-0000-0000-000000000001"),
                device_index=0,
                allocated_ratio=Decimal("0.5"),
                kernel_allocations=[],
            ),
        ]

    @pytest.fixture
    def mock_agent_repository(self, sample_agent_data: MagicMock) -> MagicMock:
        """Mock AgentRepository."""
        repository = MagicMock()
        repository.get_by_id = AsyncMock(return_value=sample_agent_data)
        repository.update_gpu_alloc_map = AsyncMock()
        repository.update_gpu_devices = AsyncMock()
        return repository

    @pytest.fixture
    def mock_agent_client(
        self,
        sample_alloc_map: dict[str, Any],
        scanned_gpu_devices: list[GPUDeviceAllocation],
    ) -> MagicMock:
        """Mock AgentClient."""
        client = MagicMock()
        client.scan_gpu_alloc_map = AsyncMock(return_value=sample_alloc_map)
        client.scan_gpu_devices = AsyncMock(
            return_value=ScanGPUDevicesResp(devices=scanned_gpu_devices)
        )
        return client

    @pytest.fixture
    def mock_agent_client_pool(self, mock_agent_client: MagicMock) -> MagicMock:
        """Mock AgentClientPool."""
        pool = MagicMock()

        # Create context manager for acquire()
        class MockAcquireContextManager:
            def __init__(self, agent_id: AgentId) -> None:
                self.agent_id = agent_id
                self.client = mock_agent_client

            async def __aenter__(self) -> MagicMock:
                return self.client

            async def __aexit__(self, *args: object) -> None:
                pass

        pool.acquire = MagicMock(side_effect=lambda agent_id: MockAcquireContextManager(agent_id))
        return pool

    @pytest.fixture
    def handler(
        self,
        mock_agent_repository: MagicMock,
        mock_agent_client_pool: MagicMock,
    ) -> RescanGPUAllocMapsHandler:
        """Create handler instance with mocked dependencies."""
        return RescanGPUAllocMapsHandler(
            agent_repository=mock_agent_repository,
            agent_client_pool=mock_agent_client_pool,
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

    async def test_execute_success(
        self,
        handler: RescanGPUAllocMapsHandler,
        mock_agent_repository: MagicMock,
        mock_agent_client_pool: MagicMock,
        mock_agent_client: MagicMock,
        sample_agent_id: AgentId,
        sample_agent_data: MagicMock,
        sample_alloc_map: dict[str, Any],
        scanned_gpu_devices: list[GPUDeviceAllocation],
    ) -> None:
        """Test successful execution scans GPU alloc map and stores in cache."""
        manifest = RescanGPUAllocMapsManifest(agent_id=sample_agent_id)

        # Execute handler (returns None)
        await handler.execute(manifest)

        # Verify repository.get_by_id was called
        mock_agent_repository.get_by_id.assert_called_once_with(sample_agent_id)

        # Verify agent_client_pool.acquire was called
        mock_agent_client_pool.acquire.assert_called_once_with(sample_agent_data.id)

        # Verify agent_client.scan_gpu_alloc_map was called
        mock_agent_client.scan_gpu_alloc_map.assert_called_once()

        # Verify repository.update_gpu_alloc_map was called with correct parameters
        mock_agent_repository.update_gpu_alloc_map.assert_called_once_with(
            sample_agent_id,
            sample_alloc_map,
        )
        mock_agent_repository.update_gpu_devices.assert_called_once_with(
            sample_agent_id,
            scanned_gpu_devices,
        )

    @pytest.fixture
    def mock_agent_client_without_device_scan(self, mock_agent_client: MagicMock) -> MagicMock:
        """Mock AgentClient of an agent that does not serve scan_gpu_devices."""
        mock_agent_client.scan_gpu_devices.side_effect = RuntimeError("no such method")
        return mock_agent_client

    @pytest.mark.usefixtures("mock_agent_client_without_device_scan")
    async def test_execute_stores_alloc_map_when_device_scan_fails(
        self,
        handler: RescanGPUAllocMapsHandler,
        mock_agent_repository: MagicMock,
        sample_agent_id: AgentId,
        sample_alloc_map: dict[str, Any],
    ) -> None:
        """Test the alloc map is stored even when the agent cannot scan its devices."""
        with pytest.raises(RuntimeError):
            await handler.execute(RescanGPUAllocMapsManifest(agent_id=sample_agent_id))

        mock_agent_repository.update_gpu_alloc_map.assert_called_once_with(
            sample_agent_id,
            sample_alloc_map,
        )
        mock_agent_repository.update_gpu_devices.assert_not_called()

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
