from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    AgentResourceSearchResult,
    ResourceAllocationData,
    ResourceAllocationSearchResult,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.resource_slot.repository import ResourceSlotRepository
from ai.backend.manager.services.resource_slot.actions.get_agent_resources import (
    GetAgentResourcesAction,
    GetAgentResourcesResult,
)
from ai.backend.manager.services.resource_slot.actions.get_kernel_allocations import (
    GetKernelAllocationsAction,
    GetKernelAllocationsResult,
)
from ai.backend.manager.services.resource_slot.actions.search_agent_resources import (
    SearchAgentResourcesAction,
    SearchAgentResourcesResult,
)
from ai.backend.manager.services.resource_slot.actions.search_resource_allocations import (
    SearchResourceAllocationsAction,
    SearchResourceAllocationsResult,
)
from ai.backend.manager.services.resource_slot.service import ResourceSlotService


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=ResourceSlotRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> ResourceSlotService:
    return ResourceSlotService(repository=mock_repository)


@pytest.fixture
def querier() -> BatchQuerier:
    return BatchQuerier(pagination=OffsetPagination(offset=0, limit=10))


class TestAgentResources:
    async def test_get_maps_rows_to_data(
        self, service: ResourceSlotService, mock_repository: MagicMock
    ) -> None:
        row = MagicMock()
        row.agent_id = "agent-1"
        row.slot_name = "cpu"
        row.capacity = Decimal("8")
        row.used = Decimal("2")
        mock_repository.get_agent_resources = AsyncMock(return_value=[row])

        result = await service.get_agent_resources(GetAgentResourcesAction(agent_id="agent-1"))

        assert isinstance(result, GetAgentResourcesResult)
        assert result.items == [
            AgentResourceData(
                agent_id="agent-1", slot_name="cpu", capacity=Decimal("8"), used=Decimal("2")
            )
        ]
        mock_repository.get_agent_resources.assert_called_once_with("agent-1")

    async def test_get_empty(
        self, service: ResourceSlotService, mock_repository: MagicMock
    ) -> None:
        mock_repository.get_agent_resources = AsyncMock(return_value=[])

        result = await service.get_agent_resources(GetAgentResourcesAction(agent_id="unknown"))

        assert result.items == []

    async def test_get_multiple_slots(
        self, service: ResourceSlotService, mock_repository: MagicMock
    ) -> None:
        rows = []
        for slot, cap in [("cpu", "8"), ("mem", "32768")]:
            r = MagicMock()
            r.agent_id = "agent-1"
            r.slot_name = slot
            r.capacity = Decimal(cap)
            r.used = Decimal("0")
            rows.append(r)
        mock_repository.get_agent_resources = AsyncMock(return_value=rows)

        result = await service.get_agent_resources(GetAgentResourcesAction(agent_id="agent-1"))

        assert len(result.items) == 2
        assert result.items[0].slot_name == "cpu"
        assert result.items[1].slot_name == "mem"

    async def test_search_passes_through(
        self,
        service: ResourceSlotService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        item = AgentResourceData(
            agent_id="agent-1", slot_name="cpu", capacity=Decimal("8"), used=Decimal("2")
        )
        mock_repository.search_agent_resources = AsyncMock(
            return_value=AgentResourceSearchResult(
                items=[item], total_count=1, has_next_page=False, has_previous_page=False
            )
        )

        result = await service.search_agent_resources(SearchAgentResourcesAction(querier=querier))

        assert isinstance(result, SearchAgentResourcesResult)
        assert result.items == [item]
        assert result.total_count == 1
        assert result.has_next_page is False
        mock_repository.search_agent_resources.assert_called_once_with(querier)

    async def test_search_empty(
        self,
        service: ResourceSlotService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        mock_repository.search_agent_resources = AsyncMock(
            return_value=AgentResourceSearchResult(
                items=[], total_count=0, has_next_page=False, has_previous_page=False
            )
        )

        result = await service.search_agent_resources(SearchAgentResourcesAction(querier=querier))

        assert result.items == []
        assert result.total_count == 0

    async def test_search_has_next_page(
        self,
        service: ResourceSlotService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.search_agent_resources = AsyncMock(
            return_value=AgentResourceSearchResult(
                items=[
                    AgentResourceData(
                        agent_id=f"agent-{i}",
                        slot_name="cpu",
                        capacity=Decimal("8"),
                        used=Decimal("0"),
                    )
                    for i in range(5)
                ],
                total_count=20,
                has_next_page=True,
                has_previous_page=True,
            )
        )
        paged_querier = BatchQuerier(pagination=OffsetPagination(offset=5, limit=5))

        result = await service.search_agent_resources(
            SearchAgentResourcesAction(querier=paged_querier)
        )

        assert result.total_count == 20
        assert result.has_next_page is True
        assert result.has_previous_page is True


class TestResourceAllocations:
    async def test_get_maps_rows_to_data(
        self, service: ResourceSlotService, mock_repository: MagicMock
    ) -> None:
        kernel_id = uuid.uuid4()
        row = MagicMock()
        row.kernel_id = kernel_id
        row.slot_name = "cpu"
        row.requested = Decimal("4")
        row.used = Decimal("2")
        mock_repository.get_kernel_allocations = AsyncMock(return_value=[row])

        result = await service.get_kernel_allocations(
            GetKernelAllocationsAction(kernel_id=kernel_id)
        )

        assert isinstance(result, GetKernelAllocationsResult)
        assert result.items == [
            ResourceAllocationData(
                kernel_id=kernel_id, slot_name="cpu", requested=Decimal("4"), used=Decimal("2")
            )
        ]
        mock_repository.get_kernel_allocations.assert_called_once_with(kernel_id)

    async def test_get_empty(
        self, service: ResourceSlotService, mock_repository: MagicMock
    ) -> None:
        kernel_id = uuid.uuid4()
        mock_repository.get_kernel_allocations = AsyncMock(return_value=[])

        result = await service.get_kernel_allocations(
            GetKernelAllocationsAction(kernel_id=kernel_id)
        )

        assert result.items == []

    async def test_get_used_is_none(
        self, service: ResourceSlotService, mock_repository: MagicMock
    ) -> None:
        kernel_id = uuid.uuid4()
        row = MagicMock()
        row.kernel_id = kernel_id
        row.slot_name = "mem"
        row.requested = Decimal("4096")
        row.used = None
        mock_repository.get_kernel_allocations = AsyncMock(return_value=[row])

        result = await service.get_kernel_allocations(
            GetKernelAllocationsAction(kernel_id=kernel_id)
        )

        assert result.items[0].used is None

    async def test_search_passes_through(
        self,
        service: ResourceSlotService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        kernel_id = uuid.uuid4()
        item = ResourceAllocationData(
            kernel_id=kernel_id, slot_name="cpu", requested=Decimal("4"), used=Decimal("2")
        )
        mock_repository.search_resource_allocations = AsyncMock(
            return_value=ResourceAllocationSearchResult(
                items=[item], total_count=1, has_next_page=False, has_previous_page=False
            )
        )

        result = await service.search_resource_allocations(
            SearchResourceAllocationsAction(querier=querier)
        )

        assert isinstance(result, SearchResourceAllocationsResult)
        assert result.items == [item]
        assert result.total_count == 1
        mock_repository.search_resource_allocations.assert_called_once_with(querier)

    async def test_search_empty(
        self,
        service: ResourceSlotService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        mock_repository.search_resource_allocations = AsyncMock(
            return_value=ResourceAllocationSearchResult(
                items=[], total_count=0, has_next_page=False, has_previous_page=False
            )
        )

        result = await service.search_resource_allocations(
            SearchResourceAllocationsAction(querier=querier)
        )

        assert result.items == []
        assert result.total_count == 0
