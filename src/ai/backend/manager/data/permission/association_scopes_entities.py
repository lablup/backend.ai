import uuid
from dataclasses import dataclass

from .id import ObjectId, ScopeId


@dataclass
class ScopeEntityMappingCreateInput:
    scope_id: ScopeId
    object_id: ObjectId


@dataclass
class ScopeEntityMappingData:
    id: uuid.UUID
    scope_id: ScopeId
    object_id: ObjectId
