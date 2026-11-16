"""Create specs for session designated agents."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_designated_agent import SessionDesignatedAgentID
from ai.backend.manager.data.session.types import SessionDesignatedAgentData
from ai.backend.manager.models.session_designated_agent.row import SessionDesignatedAgentRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = ("SessionDesignatedAgentCreator",)


@dataclass(frozen=True)
class SessionDesignatedAgentCreator(
    FieldCreator[SessionID, SessionDesignatedAgentRow, SessionDesignatedAgentData]
):
    """Record one agent the session being enqueued designates."""

    agent_uuid: AgentUUID

    @override
    def field_id(self, row: SessionDesignatedAgentRow) -> SessionDesignatedAgentID:
        return SessionDesignatedAgentID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: SessionID) -> SessionDesignatedAgentRow:
        return SessionDesignatedAgentRow(session_id=owner_id, agent_uuid=self.agent_uuid)

    @override
    def to_data(self, row: SessionDesignatedAgentRow) -> SessionDesignatedAgentData:
        return SessionDesignatedAgentData(
            id=SessionDesignatedAgentID(row.id),
            session_id=SessionID(row.session_id),
            agent_uuid=AgentUUID(row.agent_uuid),
        )
