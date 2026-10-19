"""Agents a session designates for its placement."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_designated_agent import SessionDesignatedAgentID
from ai.backend.manager.models.base import GUID, Base

__all__ = ("SessionDesignatedAgentRow",)


class SessionDesignatedAgentRow(Base):
    """One row per (session, agent) designation.

    Deleting either the session or the agent deletes the row.
    """

    __tablename__ = "session_designated_agents"

    id: Mapped[SessionDesignatedAgentID] = mapped_column(
        "id",
        GUID(SessionDesignatedAgentID),
        unique=True,
        nullable=False,
        server_default=sa.text("uuid_generate_v7()"),
    )
    session_id: Mapped[SessionID] = mapped_column("session_id", GUID(SessionID), primary_key=True)
    agent_uuid: Mapped[AgentUUID] = mapped_column(
        "agent_uuid", GUID(AgentUUID), primary_key=True, index=True
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_uuid"], ["agents.uuid"], ondelete="CASCADE"),
    )
