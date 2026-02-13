"""
Tests for AgentAdapter.
Tests the adapter layer for converting request DTOs to BatchQuerier objects
and AgentDetailData to AgentDTO.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from ai.backend.common.dto.manager.agent.request import (
    AgentFilter,
    AgentOrder,
    SearchAgentsRequest,
)
from ai.backend.common.dto.manager.agent.response import AgentDTO
from ai.backend.common.dto.manager.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusEnumFilter,
    OrderDirection,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.api.agent.agent_adapter import AgentAdapter
from ai.backend.manager.data.agent.types import AgentData, AgentDetailData, AgentStatus
from ai.backend.manager.repositories.base import OffsetPagination


class TestAgentAdapterBuildQuerier:
    """Tests for AgentAdapter.build_querier method."""

    @pytest.fixture
    def adapter(self) -> AgentAdapter:
        """Create AgentAdapter instance."""
        return AgentAdapter()

    def test_build_querier_no_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier without any filters."""
        limit = 10
        offset = 0
        request = SearchAgentsRequest(
            filter=None,
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(request)

        assert querier.conditions == []
        assert querier.orders == []
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == limit
        assert querier.pagination.offset == offset

    def test_build_querier_with_status_equals_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier with status equals filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                status=AgentStatusEnumFilter(equals=AgentStatusEnum.ALIVE),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_status_in_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier with status in filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                status=AgentStatusEnumFilter(
                    in_=[AgentStatusEnum.ALIVE, AgentStatusEnum.LOST],
                ),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_status_not_equals_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier with status not_equals filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                status=AgentStatusEnumFilter(not_equals=AgentStatusEnum.TERMINATED),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_status_not_in_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier with status not_in filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                status=AgentStatusEnumFilter(
                    not_in=[AgentStatusEnum.TERMINATED, AgentStatusEnum.LOST],
                ),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_resource_group_equals_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier with resource group equals filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                resource_group=StringFilter(equals="default"),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_resource_group_contains_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier with resource group contains filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                resource_group=StringFilter(contains="gpu"),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_resource_group_starts_with_filter(
        self, adapter: AgentAdapter
    ) -> None:
        """Test building querier with resource group starts_with filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                resource_group=StringFilter(starts_with="prod"),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_resource_group_i_contains_filter(
        self, adapter: AgentAdapter
    ) -> None:
        """Test building querier with resource group case-insensitive contains filter."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                resource_group=StringFilter(i_contains="GPU"),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_with_combined_filters(self, adapter: AgentAdapter) -> None:
        """Test building querier with both status and scaling group filters."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                status=AgentStatusEnumFilter(
                    in_=[AgentStatusEnum.ALIVE],
                ),
                resource_group=StringFilter(equals="gpu-group"),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 2
        assert all(callable(c) for c in querier.conditions)

    def test_build_querier_with_ordering_id_asc(self, adapter: AgentAdapter) -> None:
        """Test building querier with id ascending order."""
        request = SearchAgentsRequest(
            filter=None,
            order=[
                AgentOrder(
                    field=AgentOrderField.ID,
                    direction=OrderDirection.ASC,
                )
            ],
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1

    def test_build_querier_with_ordering_status_desc(self, adapter: AgentAdapter) -> None:
        """Test building querier with status descending order."""
        request = SearchAgentsRequest(
            filter=None,
            order=[
                AgentOrder(
                    field=AgentOrderField.STATUS,
                    direction=OrderDirection.DESC,
                )
            ],
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1

    def test_build_querier_with_ordering_resource_group(self, adapter: AgentAdapter) -> None:
        """Test building querier with resource_group order."""
        request = SearchAgentsRequest(
            filter=None,
            order=[
                AgentOrder(
                    field=AgentOrderField.RESOURCE_GROUP,
                    direction=OrderDirection.ASC,
                )
            ],
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1

    def test_build_querier_with_pagination(self, adapter: AgentAdapter) -> None:
        """Test building querier with custom pagination."""
        limit = 20
        offset = 40
        request = SearchAgentsRequest(
            filter=None,
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(request)

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == limit
        assert querier.pagination.offset == offset

    def test_build_querier_with_empty_status_in_filter(self, adapter: AgentAdapter) -> None:
        """Test building querier with empty status in_ list does not add condition."""
        request = SearchAgentsRequest(
            filter=AgentFilter(
                status=AgentStatusEnumFilter(in_=[]),
            ),
            order=None,
            limit=50,
            offset=0,
        )

        querier = adapter.build_querier(request)

        assert querier.conditions == []


class TestAgentAdapterConvertToDTO:
    """Tests for AgentAdapter.convert_to_dto method."""

    @pytest.fixture
    def adapter(self) -> AgentAdapter:
        """Create AgentAdapter instance."""
        return AgentAdapter()

    def _make_agent_detail_data(
        self,
        *,
        agent_id: AgentId | None = None,
        status: AgentStatus = AgentStatus.ALIVE,
        region: str = "us-east-1",
        scaling_group: str = "default",
        schedulable: bool = True,
        available_slots: ResourceSlot | None = None,
        occupied_slots: ResourceSlot | None = None,
        addr: str = "tcp://127.0.0.1:6001",
        architecture: str = "x86_64",
        version: str = "24.12.0",
    ) -> AgentDetailData:
        if agent_id is None:
            agent_id = AgentId("i-test-agent-001")
        if available_slots is None:
            available_slots = ResourceSlot()
        if occupied_slots is None:
            occupied_slots = ResourceSlot()
        agent = AgentData(
            id=agent_id,
            status=status,
            status_changed=None,
            region=region,
            scaling_group=scaling_group,
            schedulable=schedulable,
            available_slots=available_slots,
            cached_occupied_slots=occupied_slots,
            actual_occupied_slots=ResourceSlot(),
            addr=addr,
            public_host=None,
            first_contact=None,
            lost_at=None,
            version=version,
            architecture=architecture,
            compute_plugins={},
            public_key=None,
            auto_terminate_abusing_kernel=False,
        )
        return AgentDetailData(agent=agent, permissions=[])

    def test_convert_basic(self, adapter: AgentAdapter) -> None:
        """Test basic conversion of AgentDetailData to AgentDTO."""
        data = self._make_agent_detail_data()

        dto = adapter.convert_to_dto(data)

        assert isinstance(dto, AgentDTO)
        assert dto.id == "i-test-agent-001"
        assert dto.status == "ALIVE"
        assert dto.region == "us-east-1"
        assert dto.resource_group == "default"
        assert dto.schedulable is True
        assert dto.addr == "tcp://127.0.0.1:6001"
        assert dto.architecture == "x86_64"
        assert dto.version == "24.12.0"

    def test_convert_resource_slots(self, adapter: AgentAdapter) -> None:
        """Test ResourceSlot serialization in DTO conversion."""
        available = ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")})
        occupied = ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")})
        data = self._make_agent_detail_data(
            available_slots=available,
            occupied_slots=occupied,
        )

        dto = adapter.convert_to_dto(data)

        assert dto.available_slots == {"cpu": "4", "mem": "8589934592"}
        assert dto.occupied_slots == {"cpu": "2", "mem": "4294967296"}

    def test_convert_empty_resource_slots(self, adapter: AgentAdapter) -> None:
        """Test conversion with empty ResourceSlots."""
        data = self._make_agent_detail_data(
            available_slots=ResourceSlot(),
            occupied_slots=ResourceSlot(),
        )

        dto = adapter.convert_to_dto(data)

        assert dto.available_slots == {}
        assert dto.occupied_slots == {}

    def test_convert_status_name_mapping(self, adapter: AgentAdapter) -> None:
        """Test that each agent status maps to the correct name string."""
        for status in AgentStatus:
            data = self._make_agent_detail_data(status=status)
            dto = adapter.convert_to_dto(data)
            assert dto.status == status.name

    def test_convert_non_schedulable_agent(self, adapter: AgentAdapter) -> None:
        """Test conversion of a non-schedulable agent."""
        data = self._make_agent_detail_data(schedulable=False)

        dto = adapter.convert_to_dto(data)

        assert dto.schedulable is False
