import uuid
from dataclasses import dataclass

from .id import ObjectId, ScopeId


@dataclass
class AssociationScopesEntitiesData:
    id: uuid.UUID
    scope_id: ScopeId
    object_id: ObjectId
