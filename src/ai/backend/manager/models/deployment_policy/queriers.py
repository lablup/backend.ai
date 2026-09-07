"""Querier specs for the deployment_policies table."""

from __future__ import annotations

from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.specs.querier import OwnedFieldQuerier


class DeploymentPolicyByDeploymentQuerier(
    OwnedFieldQuerier[DeploymentID, DeploymentPolicyRow, DeploymentPolicyData]
):
    """The policy a deployment carries; ``uq_deployment_policies_endpoint`` caps it at one."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentPolicyRow)

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return DeploymentPolicyRow.endpoint

    @override
    def to_data(self, row: DeploymentPolicyRow) -> DeploymentPolicyData:
        return row.to_data()
