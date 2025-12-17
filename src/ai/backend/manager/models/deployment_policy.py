from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import relationship

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.deployment import InvalidDeploymentStrategy

from .base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    pass

__all__ = (
    "DeploymentPolicyRow",
    "DeploymentPolicyData",
    "RollingUpdateSpec",
    "BlueGreenSpec",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class RollingUpdateSpec(BaseModel):
    """Specification for rolling update deployment strategy."""

    max_surge: int = 1
    max_unavailable: int = 0


class BlueGreenSpec(BaseModel):
    """Specification for blue-green deployment strategy."""

    auto_promote: bool = False
    promote_delay_seconds: int = 0


class DeploymentPolicyRow(Base):
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

    id = IDColumn()
    endpoint = sa.Column("endpoint", GUID, nullable=False)

    # Deployment strategy
    strategy = sa.Column(
        "strategy",
        StrEnumType(DeploymentStrategy, use_name=False),
        nullable=False,
    )

    # Strategy-specific specification stored as JSONB
    strategy_spec = sa.Column(
        "strategy_spec",
        pgsql.JSONB(),
        nullable=False,
        server_default="{}",
    )

    # Whether to rollback on deployment failure
    rollback_on_failure = sa.Column(
        "rollback_on_failure",
        sa.Boolean,
        nullable=False,
        server_default="false",
    )

    # Timestamps
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # Relationships (without FK constraints)
    endpoint_row = relationship(
        "EndpointRow",
        back_populates="deployment_policy",
        primaryjoin="foreign(DeploymentPolicyRow.endpoint) == EndpointRow.id",
        uselist=False,
    )

    def to_data(self) -> DeploymentPolicyData:
        """Convert to DeploymentPolicyData dataclass."""
        return DeploymentPolicyData(
            id=self.id,
            endpoint=self.endpoint,
            strategy=self.strategy,
            strategy_spec=self.get_strategy_spec(),
            rollback_on_failure=self.rollback_on_failure,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def get_strategy_spec(self) -> RollingUpdateSpec | BlueGreenSpec:
        """Parse strategy spec to the appropriate Pydantic model based on strategy type."""
        match self.strategy:
            case DeploymentStrategy.ROLLING:
                return RollingUpdateSpec.model_validate(self.strategy_spec or {})
            case DeploymentStrategy.BLUE_GREEN:
                return BlueGreenSpec.model_validate(self.strategy_spec or {})
            case _:
                raise InvalidDeploymentStrategy(f"Unknown deployment strategy: {self.strategy}")


@dataclass
class DeploymentPolicyData:
    """Data class for DeploymentPolicyRow."""

    id: UUID
    endpoint: UUID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    rollback_on_failure: bool
    created_at: datetime
    updated_at: datetime
