from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("DeploymentPolicyRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentPolicyRow(LifecycleTimestampsMixin, Base):
    """
    Represents a deployment policy for a deployment.

    Each endpoint has at most one deployment policy (1:1 relationship).
    The policy defines the deployment strategy (rolling update or blue-green)
    and its configuration.
    """

    __tablename__ = "deployment_policies"

    __table_args__ = (
        sa.UniqueConstraint("endpoint", name="uq_deployment_policies_endpoint"),
        sa.Index("ix_deployment_policies_endpoint", "endpoint"),
    )

    id: Mapped[DeploymentPolicyID] = mapped_column(
        "id",
        GUID(DeploymentPolicyID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    endpoint: Mapped[DeploymentID] = mapped_column(
        "endpoint",
        GUID(DeploymentID),
        sa.ForeignKey("endpoints.id", name="fk_deployment_policies_endpoint", ondelete="CASCADE"),
        nullable=False,
    )

    # Deployment strategy
    strategy: Mapped[DeploymentStrategy] = mapped_column(
        "strategy",
        StrEnumType(DeploymentStrategy, use_name=False),
        nullable=False,
    )

    # Strategy-specific specification stored as JSONB
    strategy_spec: Mapped[dict[str, object]] = mapped_column(
        "strategy_spec",
        pgsql.JSONB(),
        nullable=False,
        server_default="{}",
    )
