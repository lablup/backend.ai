from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.routing.searchers import ModelReplicaSearcher


@dataclass
class GlobalSearchReplicasAction(SearchGlobalOpsAction[RoutingRow, ModelReplicaData]):
    """Page through replicas across every deployment."""

    searcher: ModelReplicaSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_replicas"

    @override
    def to_searcher(self) -> ModelReplicaSearcher:
        return self.searcher
