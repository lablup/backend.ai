"""UpserterSpec for deployment policy upsert operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    DeploymentPolicyRow,
    RollingUpdateSpec,
)
from ai.backend.manager.repositories.base.upserter import UpserterSpec


@dataclass
class DeploymentPolicyUpserterSpec(UpserterSpec[DeploymentPolicyRow]):
    """UpserterSpec for deployment policy upsert (INSERT ON CONFLICT UPDATE).

    Uses the unique constraint on ``endpoint`` column to detect conflicts.
    On conflict, updates strategy, strategy_spec, and rollback_on_failure.
    """

    endpoint_id: uuid.UUID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    rollback_on_failure: bool

    @property
    @override
    def row_class(self) -> type[DeploymentPolicyRow]:
        return DeploymentPolicyRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint_id,
            "strategy": self.strategy,
            "strategy_spec": self.strategy_spec.model_dump(),
            "rollback_on_failure": self.rollback_on_failure,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "strategy_spec": self.strategy_spec.model_dump(),
            "rollback_on_failure": self.rollback_on_failure,
            "updated_at": sa.func.now(),
        }
