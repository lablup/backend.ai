import uuid
from dataclasses import dataclass

from ai.backend.manager.data.permission.id import ObjectId, ScopeId


@dataclass
class ScopeEntityMappingCreateInput:
    scope_id: ScopeId
    entity_id: ObjectId


@dataclass
class ScopeEntityMappingData:
    id: uuid.UUID
    scope_id: ScopeId
    entity_id: ObjectId
