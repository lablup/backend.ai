from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.errors.deployment import InvalidDeploymentStrategy
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

if TYPE_CHECKING:
    from ai.backend.manager.models.endpoint import EndpointRow

__all__ = ("DeploymentPolicyRow",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentPolicyRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
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
    endpoint: Mapped[DeploymentID] = mapped_column(
        "endpoint",
        GUID,
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

    endpoint_row: Mapped[EndpointRow | None] = relationship(
        "EndpointRow",
        back_populates="deployment_policy",
        foreign_keys=[endpoint],
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
