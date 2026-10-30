"""Querier implementations for deployments, endpoint tokens and auto-scaling rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.manager.data.deployment.types import (
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelDeploymentData,
)
from ai.backend.manager.models.endpoint.row import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.endpoint.searchable_fields import (
    AutoScalingRuleSearchableFields,
    DeploymentAccessTokenSearchableFields,
    DeploymentSearchableFields,
)
from ai.backend.manager.models.specs.querier import (
    BulkEntityQuerier,
    BulkFieldQuerier,
    FieldQuerier,
)


@dataclass
class DeploymentAccessTokenQuerier(FieldQuerier[EndpointTokenRow, ModelDeploymentAccessTokenData]):
    access_token_id: DeploymentTokenID

    @override
    def row_class(self) -> type[EndpointTokenRow]:
        return EndpointTokenRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointTokenRow.id

    @override
    def target_id_value(self) -> DeploymentTokenID:
        return self.access_token_id

    @override
    def to_data(self, row: EndpointTokenRow) -> ModelDeploymentAccessTokenData:
        return DeploymentAccessTokenSearchableFields.own.to_data(row)


class BulkDeploymentQuerier(BulkEntityQuerier[EndpointRow, ModelDeploymentData]):
    """The deployments the caller named."""

    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointRow.id

    @override
    def to_data(self, row: EndpointRow) -> ModelDeploymentData:
        return DeploymentSearchableFields.own.to_data(row)


class BulkAutoScalingRuleQuerier(
    BulkFieldQuerier[EndpointAutoScalingRuleRow, ModelDeploymentAutoScalingRuleData]
):
    """The auto-scaling rules the caller named."""

    @override
    def row_class(self) -> type[EndpointAutoScalingRuleRow]:
        return EndpointAutoScalingRuleRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointAutoScalingRuleRow.id

    @override
    def to_data(self, row: EndpointAutoScalingRuleRow) -> ModelDeploymentAutoScalingRuleData:
        return AutoScalingRuleSearchableFields.own.to_data(row)


class BulkDeploymentAccessTokenQuerier(
    BulkFieldQuerier[EndpointTokenRow, ModelDeploymentAccessTokenData]
):
    """The access tokens the caller named."""

    @override
    def row_class(self) -> type[EndpointTokenRow]:
        return EndpointTokenRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EndpointTokenRow.id

    @override
    def to_data(self, row: EndpointTokenRow) -> ModelDeploymentAccessTokenData:
        return DeploymentAccessTokenSearchableFields.own.to_data(row)
