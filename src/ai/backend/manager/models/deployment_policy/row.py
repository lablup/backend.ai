from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.deployment import InvalidDeploymentStrategy
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.endpoint import EndpointRow

__all__ = (
    "BlueGreenSpec",
    "DeploymentPolicyData",
    "DeploymentPolicyRow",
    "RollingUpdateSpec",
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


def _get_endpoint_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.endpoint import EndpointRow

    return foreign(DeploymentPolicyRow.endpoint) == EndpointRow.id


class DeploymentPolicyRow(Base):  # type: ignore[misc]
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

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    endpoint: Mapped[uuid.UUID] = mapped_column("endpoint", GUID, nullable=False)

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

    # Whether to rollback on deployment failure
    rollback_on_failure: Mapped[bool] = mapped_column(
        "rollback_on_failure",
        sa.Boolean,
        nullable=False,
        server_default="false",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # Relationships (without FK constraints)
    endpoint_row: Mapped[EndpointRow | None] = relationship(
        "EndpointRow",
        back_populates="deployment_policy",
        primaryjoin=_get_endpoint_join_condition,
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

    id: uuid.UUID
    endpoint: uuid.UUID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    rollback_on_failure: bool
    created_at: datetime
    updated_at: datetime
