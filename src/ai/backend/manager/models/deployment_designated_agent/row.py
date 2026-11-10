"""Agents a deployment designates for its route sessions."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.models.base import GUID, Base

__all__ = ("DeploymentDesignatedAgentRow",)


class DeploymentDesignatedAgentRow(Base):
    """One row per (deployment, agent) designation.

    Deleting either the deployment or the agent deletes the row.
    """

    __tablename__ = "deployment_designated_agents"

    endpoint_id: Mapped[DeploymentID] = mapped_column(
        "endpoint_id", GUID(DeploymentID), primary_key=True
    )
    agent_uuid: Mapped[AgentUUID] = mapped_column(
        "agent_uuid", GUID(AgentUUID), primary_key=True, index=True
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_uuid"], ["agents.uuid"], ondelete="CASCADE"),
    )
