from collections.abc import Collection

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.resource_slot import AgentResourceRow, ResourceSlotTypeRow


async def fetch_actual_occupied_slots(
    db_session: SASession,
    agent_ids: Collection[AgentId],
) -> dict[AgentId, ResourceSlot]:
    """Load per-agent occupied slots from ``agent_resources``, keyed in slot type rank order."""
    occupied: dict[AgentId, ResourceSlot] = {
        AgentId(agent_id): ResourceSlot() for agent_id in agent_ids
    }
    if not occupied:
        return occupied
    stmt = (
        sa.select(AgentResourceRow.agent_id, AgentResourceRow.slot_name, AgentResourceRow.used)
        .join(
            ResourceSlotTypeRow,
            AgentResourceRow.slot_name == ResourceSlotTypeRow.slot_name,
        )
        .where(AgentResourceRow.agent_id.in_(occupied.keys()))
        .order_by(ResourceSlotTypeRow.rank)
    )
    for row in await db_session.execute(stmt):
        occupied[AgentId(row.agent_id)][row.slot_name] = row.used
    return occupied


class QueryConditions:
    @staticmethod
    def by_ids(agent_ids: Collection[AgentId]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.id.in_(agent_ids)

        return inner

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.scaling_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"%{spec.value}%")
            else:
                condition = AgentRow.scaling_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AgentRow.scaling_group) == spec.value.lower()
            else:
                condition = AgentRow.scaling_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"{spec.value}%")
            else:
                condition = AgentRow.scaling_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AgentRow.scaling_group.ilike(f"%{spec.value}")
            else:
                condition = AgentRow.scaling_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_resource_group_in = staticmethod(make_string_in_factory(AgentRow.scaling_group))

    @staticmethod
    def by_statuses(statuses: Collection[AgentStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_equals(status: AgentStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status == status

        return inner

    @staticmethod
    def by_status_not_equals(status: AgentStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status != status

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[AgentStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentRow.status.not_in(statuses)

        return inner


class QueryOrders:
    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.id.asc()
        return AgentRow.id.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.status.asc()
        return AgentRow.status.desc()

    @staticmethod
    def resource_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.scaling_group.asc()
        return AgentRow.scaling_group.desc()
