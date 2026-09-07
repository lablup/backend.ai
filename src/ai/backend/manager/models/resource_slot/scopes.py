"""Operation scopes for the resource slot rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_slot.row import AgentResourceRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = ("AgentResourceOperationScope",)


@dataclass(frozen=True)
class AgentResourceOperationScope(OperationScope):
    """The slot rows of one agent; the row names the agent by ``agents.id``."""

    agent_uuid: AgentUUID

    @override
    def to_condition(self) -> QueryCondition:
        agent_uuid = self.agent_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AgentResourceRow.agent_id == (
                sa.select(AgentRow.id).where(AgentRow.uuid == agent_uuid).scalar_subquery()
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
