from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.etcd_config import ETCD_CONFIG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AcceleratorMetadata
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class GetResourceMetadataAction(BaseGlobalAction):
    """Action to get resource metadata with optional scaling group filter."""

    sgroup: str | None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ETCD_CONFIG_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_resource_metadata"


@dataclass
class GetResourceMetadataActionResult:
    """Result of getting resource metadata."""

    metadata: dict[str, AcceleratorMetadata]
