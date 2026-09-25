"""What a deployment policy search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.errors.deployment import InvalidDeploymentStrategy
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _DeploymentPolicyOwnFields(RowDataConverter[DeploymentPolicyRow, DeploymentPolicyData]):
    """The policy's own columns.

    ``strategy_spec`` is JSONB, so it carries neither a filter nor an order. Which
    model it parses into is decided by ``strategy``.
    """

    id = SearchableField(
        DeploymentPolicyRow.id,
        UUIDConditions(DeploymentPolicyRow.id),
        ColumnOrder(DeploymentPolicyRow.id),
    )
    endpoint = SearchableField(
        DeploymentPolicyRow.endpoint,
        UUIDConditions(DeploymentPolicyRow.endpoint),
        ColumnOrder(DeploymentPolicyRow.endpoint),
    )
    strategy = SearchableField(
        DeploymentPolicyRow.strategy,
        EnumConditions(DeploymentPolicyRow.strategy, DeploymentStrategy),
        ColumnOrder(DeploymentPolicyRow.strategy),
    )
    strategy_spec = SearchableField(DeploymentPolicyRow.strategy_spec, None, None)
    created_at = SearchableField(
        DeploymentPolicyRow.created_at,
        DateTimeConditions(DeploymentPolicyRow.created_at),
        ColumnOrder(DeploymentPolicyRow.created_at),
    )
    updated_at = SearchableField(
        DeploymentPolicyRow.updated_at,
        DateTimeConditions(DeploymentPolicyRow.updated_at),
        ColumnOrder(DeploymentPolicyRow.updated_at),
    )

    @override
    def to_data(self, row: DeploymentPolicyRow) -> DeploymentPolicyData:
        return DeploymentPolicyData(
            id=self.id.read(row),
            endpoint=self.endpoint.read(row),
            strategy=self.strategy.read(row),
            strategy_spec=self._strategy_spec(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )

    def _strategy_spec(self, row: DeploymentPolicyRow) -> RollingUpdateSpec | BlueGreenSpec:
        spec = self.strategy_spec.read(row) or {}
        match self.strategy.read(row):
            case DeploymentStrategy.ROLLING:
                return RollingUpdateSpec.model_validate(spec)
            case DeploymentStrategy.BLUE_GREEN:
                return BlueGreenSpec.model_validate(spec)
            case strategy:
                raise InvalidDeploymentStrategy(f"Unknown deployment strategy: {strategy}")


class DeploymentPolicySearchableFields:
    own = _DeploymentPolicyOwnFields()
