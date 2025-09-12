import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator

from .id import ObjectId, ScopeId


@dataclass
class AssociationScopesEntitiesCreateInput(Creator):
    scope_id: ScopeId
    object_id: ObjectId

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "scope_type": self.scope_id.scope_type,
            "scope_id": self.scope_id.scope_id,
            "entity_type": self.object_id.entity_type,
            "entity_id": self.object_id.entity_id,
        }


@dataclass
class AssociationScopesEntitiesData:
    id: uuid.UUID
    scope_id: ScopeId
    object_id: ObjectId
