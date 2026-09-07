"""Searcher spec for the endpoint_tokens table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.models.endpoint.row import EndpointTokenRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class DeploymentAccessTokenSearcher(Searcher[EndpointTokenRow, ModelDeploymentAccessTokenData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(EndpointTokenRow)

    @override
    def to_data(self, row: EndpointTokenRow) -> ModelDeploymentAccessTokenData:
        return row.to_access_token_data()
