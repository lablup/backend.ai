from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentAccessTokenData
from ai.backend.manager.models.endpoint.row import EndpointTokenRow
from ai.backend.manager.models.endpoint.scopes import DeploymentAccessTokenTarget
from ai.backend.manager.models.endpoint.searchers import DeploymentAccessTokenSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchAccessTokensAction(
    BulkScopedSearchOpsAction[EndpointTokenRow, ModelDeploymentAccessTokenData]
):
    """Page through the access tokens of the deployments named, combined with OR.

    Every deployment is authorized before the read runs. Reading every deployment's
    tokens is the global variant, which says so in its shape.
    """

    deployment_ids: Sequence[DeploymentID]
    searcher: DeploymentAccessTokenSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_access_tokens"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.deployment_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            DeploymentAccessTokenTarget(deployment_id=deployment_id)
            for deployment_id in self.deployment_ids
        ]

    @override
    def to_searcher(self) -> DeploymentAccessTokenSearcher:
        return self.searcher
