from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.models.endpoint.row import EndpointTokenRow
from ai.backend.manager.models.endpoint.searchers import DeploymentAccessTokenSearcher


@dataclass
class GlobalSearchAccessTokensAction(
    SearchGlobalOpsAction[EndpointTokenRow, ModelDeploymentAccessTokenData]
):
    """Page through access tokens across every deployment."""

    searcher: DeploymentAccessTokenSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_access_tokens"

    @override
    def to_searcher(self) -> DeploymentAccessTokenSearcher:
        return self.searcher
