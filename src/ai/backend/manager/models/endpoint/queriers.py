"""FieldQuerier implementations for endpoint tokens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment_token import DeploymentTokenID
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.models.endpoint.row import EndpointTokenRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier, FieldQuerier


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
        return row.to_access_token_data()


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
        return row.to_access_token_data()
