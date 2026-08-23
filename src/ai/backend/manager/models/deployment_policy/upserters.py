"""Upsert specs for the deployment_policies table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter


@dataclass
class DeploymentPolicyUpserter(
    FieldUpserter[DeploymentID, DeploymentPolicyRow, DeploymentPolicyData]
):
    """Sets the deployment's strategy, replacing the row it already has.

    Conflicts are detected on the unique ``endpoint`` column.
    """

    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec

    @override
    def row_class(self) -> type[DeploymentPolicyRow]:
        return DeploymentPolicyRow

    @override
    def index_elements(self) -> list[str]:
        return ["endpoint"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: DeploymentID) -> dict[str, Any]:
        return {
            "endpoint": owner_id,
            "strategy": self.strategy,
            "strategy_spec": self.strategy_spec.model_dump(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "strategy_spec": self.strategy_spec.model_dump(),
            "updated_at": sa.func.now(),
        }

    @override
    def to_data(self, row: DeploymentPolicyRow) -> DeploymentPolicyData:
        return row.to_data()
