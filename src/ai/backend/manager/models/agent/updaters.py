"""Update specs for the agents table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent.conditions import AgentConditions
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater, GuardedDataUpdater
from ai.backend.manager.types import OptionalState

# The statuses an agent no longer leaves; an exit transition from one is a no-op.
TERMINAL_AGENT_STATUSES: tuple[AgentStatus, ...] = (AgentStatus.LOST, AgentStatus.TERMINATED)


@dataclass
class AgentStatusUpdater(DataUpdater[AgentRow, AgentId]):
    """Writes an agent's lifecycle status.

    Written by ``agents.uuid``: ``agents.id`` is the name an operator types, and
    writing by the key while checking by the id lets the two part ways.
    """

    agent_uuid: AgentUUID
    status: AgentStatus
    status_changed: datetime
    lost_at: OptionalState[datetime] = field(default_factory=OptionalState[datetime].nop)

    @property
    @override
    def row_class(self) -> type[AgentRow]:
        return AgentRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AgentRow.uuid

    @override
    def target_id_value(self) -> AgentUUID:
        return self.agent_uuid

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {
            "status": self.status,
            "status_changed": self.status_changed,
        }
        self.lost_at.update_dict(to_update, "lost_at")
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: AgentRow) -> AgentId:
        return AgentId(row.id)


@dataclass
class AgentExitStatusUpdater(GuardedDataUpdater[AgentRow, AgentId]):
    """Writes an agent's exit status, leaving an already terminal agent alone.

    The guard rides on the statement, so a late duplicate exit cannot overwrite the
    status recorded first.
    """

    agent_uuid: AgentUUID
    status: AgentStatus
    status_changed: datetime
    lost_at: OptionalState[datetime] = field(default_factory=OptionalState[datetime].nop)

    @property
    @override
    def row_class(self) -> type[AgentRow]:
        return AgentRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AgentRow.uuid

    @override
    def target_id_value(self) -> AgentUUID:
        return self.agent_uuid

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [AgentConditions.by_status_not_in(TERMINAL_AGENT_STATUSES)]

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {
            "status": self.status,
            "status_changed": self.status_changed,
        }
        self.lost_at.update_dict(to_update, "lost_at")
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: AgentRow) -> AgentId:
        return AgentId(row.id)
