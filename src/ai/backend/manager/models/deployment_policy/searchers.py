"""List-read spec for deployment policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_policy.searchable_fields import (
    DeploymentPolicySearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class DeploymentPolicySearcher(Searcher[DeploymentPolicyRow, DeploymentPolicyData]):
    """Deployment policies matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentPolicyRow)

    @override
    def to_data(self, row: DeploymentPolicyRow) -> DeploymentPolicyData:
        return DeploymentPolicySearchableFields.own.to_data(row)
