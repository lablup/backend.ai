from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class StorageNamespaceGlobalAction(BaseGlobalAction):
    """Base for the namespace operations the service still owns."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return STORAGE_NAMESPACE_ENTITY_TYPE
