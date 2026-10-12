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


@dataclass(frozen=True)
class _ReservationFilterCase:
    name: str
    filter: AgentResourceFilter


@dataclass(frozen=True)
class _ReservedRow:
    slot_name: str
    reserved: Decimal
    prereserved: Decimal


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
    @pytest.mark.parametrize(
        "case",
        [
            _ReservationFilterCase(
                name="reserved",
                filter=AgentResourceFilter(reserved=DecimalFilter(greater_than=Decimal(0))),
            ),
            _ReservationFilterCase(
                name="prereserved",
                filter=AgentResourceFilter(prereserved=DecimalFilter(greater_than=Decimal(0))),
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_filter_keeps_the_reserved_row(
        self,
        repository: OpsRepository[AgentResourceData],
        agent_uuid: AgentUUID,
        adapter: ResourceSlotAdapter,
        case: _ReservationFilterCase,
    ) -> None:
        result = await repository.search_in_scopes(
            [AgentResourceTarget(agent_uuid=agent_uuid)],
            AgentResourceSearcher(
                pagination=OffsetPagination(offset=0, limit=20),
                conditions=adapter._convert_agent_resource_filter(case.filter),
            ),
        )

        assert [
            _ReservedRow(
                slot_name=item.slot_name, reserved=item.reserved, prereserved=item.prereserved
            )
            for item in result.items
        ] == [_ReservedRow(slot_name="cpu", reserved=Decimal("1.25"), prereserved=Decimal("0.5"))]

    @pytest.mark.parametrize(
        "field",
        [AgentResourceOrderField.RESERVED, AgentResourceOrderField.PRERESERVED],
        ids=lambda field: field.value,
    )
    async def test_descending_order_overrides_the_rank(
        self,
        repository: OpsRepository[AgentResourceData],
        agent_uuid: AgentUUID,
        adapter: ResourceSlotAdapter,
        field: AgentResourceOrderField,
    ) -> None:
        result = await repository.search_in_scopes(
            [AgentResourceTarget(agent_uuid=agent_uuid)],
            AgentResourceSearcher(
                pagination=OffsetPagination(offset=0, limit=20),
                orders=adapter._convert_agent_resource_orders([
                    AgentResourceOrder(field=field, direction=OrderDirection.DESC)
                ]),
            ),
        )

        assert [item.slot_name for item in result.items] == ["cpu", "mem"]
