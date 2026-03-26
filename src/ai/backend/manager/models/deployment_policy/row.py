from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Annotated

import sqlalchemy as sa
from pydantic import BaseModel, BeforeValidator, Field, model_validator
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.types import resolve_int_or_percent, validate_int_or_percent
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
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
    "DeploymentPolicyRow",
    "DeploymentStrategySpec",
    "RollingUpdateSpec",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


IntOrPercent = Annotated[int | str, BeforeValidator(validate_int_or_percent)]


class RollingUpdateSpec(BaseModel):
    """Specification for rolling update deployment strategy.

    ``max_surge`` and ``max_unavailable`` accept either an absolute integer
    (e.g. ``1``) or a percentage string (e.g. ``"25%"``).  Percentage values
    are resolved to absolute counts at execution time via
    :meth:`resolve_max_surge` / :meth:`resolve_max_unavailable`.
    """

    max_surge: IntOrPercent = Field(default=1)
    max_unavailable: IntOrPercent = Field(default=0)

    @model_validator(mode="after")
    def _validate_progress_is_possible(self) -> RollingUpdateSpec:
        """Ensure at least one of max_surge or max_unavailable is positive.

        If both are zero (or "0%"), the rolling update FSM cannot make
        progress: it cannot create new routes (would exceed max_total)
        nor terminate old routes (would fall below min_available), causing
        a deadlock.

        When either value is a percentage string we cannot fully validate
        at definition time (the resolved count depends on the replica count
        at execution time), so we only reject the obvious ``0 + 0`` case.
        """
        if self.max_surge in (0, "0%") and self.max_unavailable in (0, "0%"):
            raise ValueError(
                "At least one of max_surge or max_unavailable must be positive; "
                "otherwise the rolling update cannot make progress."
            )
        return self

    def resolve_max_surge(self, desired_replicas: int) -> int:
        """Resolve max_surge to an absolute count (rounds up for percentages)."""
        return resolve_int_or_percent(self.max_surge, desired_replicas, round_up=True)

    def resolve_max_unavailable(self, desired_replicas: int) -> int:
        """Resolve max_unavailable to an absolute count (rounds down for percentages)."""
        return resolve_int_or_percent(self.max_unavailable, desired_replicas, round_up=False)


class BlueGreenSpec(BaseModel):
    """Specification for blue-green deployment strategy."""

    auto_promote: bool = False
    promote_delay_seconds: int = 0


DeploymentStrategySpec = RollingUpdateSpec | BlueGreenSpec


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
