"""The slot rows of an agent, read as field rows through the v2 specs.

The rows name the agent by ``agents.id`` while the entity id is ``agents.uuid``, so
both the owner lookup and the operation scope cross that join.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.dto.manager.query import DecimalFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AgentResourceFilter,
    AgentResourceOrder,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    AgentResourceOrderField,
    OrderDirection,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.resource_slot.lookups import AgentResourceOwnerLookup
from ai.backend.manager.models.resource_slot.row import AgentResourceRow, ResourceSlotTypeRow
from ai.backend.manager.models.resource_slot.scopes import AgentResourceTarget
from ai.backend.manager.models.resource_slot.searchers import AgentResourceSearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider


@dataclass(frozen=True, kw_only=True)
class ReservationComparisonCase:
    name: str
    condition: DecimalFilter
    expected_slot_names: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class ReservationOrderCase:
    direction: OrderDirection
    expected_slot_names: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class CombinedReservationFilterCase:
    name: str
    filter: AgentResourceFilter
    expected_slot_names: tuple[str, ...]


def _searcher() -> AgentResourceSearcher:
    return AgentResourceSearcher(pagination=OffsetPagination(offset=0, limit=20))


@pytest.fixture
async def agent_uuid(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine, agent_id: str
) -> AgentUUID:
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count", rank=40))
        db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes", rank=10))
        await db_sess.flush()
        found = await db_sess.scalar(sa.select(AgentRow.uuid).where(AgentRow.id == agent_id))
        assert found is not None
        owner = AgentUUID(found)
        db_sess.add(
            AgentResourceRow(
                agent_id=agent_id,
                agent_uuid=owner,
                slot_name="cpu",
                capacity=Decimal(4),
                reserved=Decimal("1.25"),
                prereserved=Decimal("0.5"),
                used=Decimal(1),
            )
        )
        db_sess.add(
            AgentResourceRow(
                agent_id=agent_id,
                agent_uuid=owner,
                slot_name="mem",
                capacity=Decimal(1024),
                used=Decimal(512),
            )
        )
        await db_sess.flush()
        return owner


@pytest.fixture
def repository(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> OpsRepository[AgentResourceData]:
    return OpsRepository[AgentResourceData](V2DBOpsProvider(database_with_resource_slot_tables))


async def test_scope_reads_one_agent_s_rows_in_rank_order(
    repository: OpsRepository[AgentResourceData], agent_uuid: AgentUUID
) -> None:
    result = await repository.search_in_scopes(
        [AgentResourceTarget(agent_uuid=agent_uuid)], _searcher()
    )

    assert [item.slot_name for item in result.items] == ["mem", "cpu"]


async def test_scope_of_an_unknown_agent_reads_nothing(
    repository: OpsRepository[AgentResourceData], agent_uuid: AgentUUID
) -> None:
    result = await repository.search_in_scopes(
        [AgentResourceTarget(agent_uuid=AgentUUID(uuid.uuid4()))],
        _searcher(),
    )

    assert result.items == []


async def test_owner_lookup_crosses_to_the_agent_uuid(
    repository: OpsRepository[AgentResourceData], agent_uuid: AgentUUID
) -> None:
    rows = await repository.search_in_scopes(
        [AgentResourceTarget(agent_uuid=agent_uuid)], _searcher()
    )
    row_ids = [item.id for item in rows.items]
    absent = AgentResourceID(uuid.uuid4())

    owners = await repository.field_owners(AgentResourceOwnerLookup(), [*row_ids, absent])

    assert owners == dict.fromkeys(row_ids, agent_uuid)


@pytest.fixture
def adapter() -> ResourceSlotAdapter:
    return ResourceSlotAdapter(MagicMock(), MagicMock(), MagicMock())


class TestAgentReservations:
    async def test_stored_reservations_are_returned(
        self, repository: OpsRepository[AgentResourceData], agent_uuid: AgentUUID
    ) -> None:
        result = await repository.search_in_scopes(
            [AgentResourceTarget(agent_uuid=agent_uuid)], _searcher()
        )
        assert [(item.slot_name, item.reserved, item.prereserved) for item in result.items] == [
            ("mem", Decimal(0), Decimal(0)),
            ("cpu", Decimal("1.25"), Decimal("0.5")),
        ]

    @pytest.mark.parametrize("field", ["reserved", "prereserved"])
    @pytest.mark.parametrize(
        "case",
        [
            ReservationComparisonCase(
                name="equals",
                condition=DecimalFilter(equals=Decimal("0")),
                expected_slot_names=("mem",),
            ),
            ReservationComparisonCase(
                name="not_equals",
                condition=DecimalFilter(not_equals=Decimal("0")),
                expected_slot_names=("cpu",),
            ),
            ReservationComparisonCase(
                name="greater_than",
                condition=DecimalFilter(greater_than=Decimal("0")),
                expected_slot_names=("cpu",),
            ),
            ReservationComparisonCase(
                name="greater_than_or_equal",
                condition=DecimalFilter(greater_than_or_equal=Decimal("0")),
                expected_slot_names=("mem", "cpu"),
            ),
            ReservationComparisonCase(
                name="less_than",
                condition=DecimalFilter(less_than=Decimal("0")),
                expected_slot_names=(),
            ),
            ReservationComparisonCase(
                name="less_than_or_equal",
                condition=DecimalFilter(less_than_or_equal=Decimal("0")),
                expected_slot_names=("mem",),
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_filter_reservations(
        self,
        repository: OpsRepository[AgentResourceData],
        agent_uuid: AgentUUID,
        adapter: ResourceSlotAdapter,
        field: str,
        case: ReservationComparisonCase,
    ) -> None:
        filter = AgentResourceFilter.model_validate({field: case.condition})
        result = await repository.search_in_scopes(
            [AgentResourceTarget(agent_uuid=agent_uuid)],
            AgentResourceSearcher(
                pagination=OffsetPagination(offset=0, limit=20),
                conditions=adapter._convert_agent_resource_filter(filter),
            ),
        )
        assert tuple(item.slot_name for item in result.items) == case.expected_slot_names

    @pytest.mark.parametrize(
        "field", [AgentResourceOrderField.RESERVED, AgentResourceOrderField.PRERESERVED]
    )
    @pytest.mark.parametrize(
        "case",
        [
            ReservationOrderCase(direction=OrderDirection.ASC, expected_slot_names=("mem", "cpu")),
            ReservationOrderCase(direction=OrderDirection.DESC, expected_slot_names=("cpu", "mem")),
        ],
        ids=lambda case: case.direction.value,
    )
    async def test_order_reservations(
        self,
        repository: OpsRepository[AgentResourceData],
        agent_uuid: AgentUUID,
        adapter: ResourceSlotAdapter,
        field: AgentResourceOrderField,
        case: ReservationOrderCase,
    ) -> None:
        result = await repository.search_in_scopes(
            [AgentResourceTarget(agent_uuid=agent_uuid)],
            AgentResourceSearcher(
                pagination=OffsetPagination(offset=0, limit=20),
                orders=adapter._convert_agent_resource_orders([
                    AgentResourceOrder(field=field, direction=case.direction)
                ]),
            ),
        )
        assert tuple(item.slot_name for item in result.items) == case.expected_slot_names

    @pytest.mark.parametrize(
        "case",
        [
            CombinedReservationFilterCase(
                name="and",
                filter=AgentResourceFilter(
                    AND=[
                        AgentResourceFilter(reserved=DecimalFilter(greater_than=Decimal("0"))),
                        AgentResourceFilter(prereserved=DecimalFilter(equals=Decimal("0.5"))),
                    ]
                ),
                expected_slot_names=("cpu",),
            ),
            CombinedReservationFilterCase(
                name="or_with_multiple_fields",
                filter=AgentResourceFilter(
                    OR=[
                        AgentResourceFilter(
                            reserved=DecimalFilter(equals=Decimal("0")),
                            prereserved=DecimalFilter(greater_than=Decimal("0")),
                        ),
                        AgentResourceFilter(reserved=DecimalFilter(equals=Decimal("1.25"))),
                    ]
                ),
                expected_slot_names=("cpu",),
            ),
            CombinedReservationFilterCase(
                name="not",
                filter=AgentResourceFilter(
                    NOT=[AgentResourceFilter(reserved=DecimalFilter(greater_than=Decimal("0")))]
                ),
                expected_slot_names=("mem",),
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_combined_reservation_filters(
        self,
        repository: OpsRepository[AgentResourceData],
        agent_uuid: AgentUUID,
        adapter: ResourceSlotAdapter,
        case: CombinedReservationFilterCase,
    ) -> None:
        input = AdminSearchAgentResourcesInput(filter=case.filter)
        querier = adapter._build_agent_resource_querier(input)
        result = await repository.search_in_scopes(
            [AgentResourceTarget(agent_uuid=agent_uuid)],
            AgentResourceSearcher(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            ),
        )
        assert tuple(item.slot_name for item in result.items) == case.expected_slot_names
