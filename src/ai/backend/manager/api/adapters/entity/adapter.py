"""Entity adapter answering what the manager has entity types for."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.entity.response import (
    EntityTypeNode,
    ListEntityTypesPayload,
)
from ai.backend.manager.api.adapters.entity.types import WiredEntityTypes


class EntityAdapter:
    """Adapter for reads over the entity types themselves."""

    _entity_types: WiredEntityTypes

    def __init__(self, entity_types: WiredEntityTypes) -> None:
        self._entity_types = entity_types

    def list_entity_types(self) -> ListEntityTypesPayload:
        """Every entity type a request may name."""
        return ListEntityTypesPayload(
            items=[
                EntityTypeNode(
                    name=str(entity_type),
                    scope_types=[
                        str(scope_type)
                        for scope_type in self._entity_types.scope_types(entity_type)
                    ],
                )
                for entity_type in self._entity_types.all()
            ]
        )


__all__ = ("EntityAdapter",)
