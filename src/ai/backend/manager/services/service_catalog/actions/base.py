from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class ServiceCatalogAction(BaseAction):
    """Base action class for service catalog operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SERVICE_CATALOG
