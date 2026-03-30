from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.permission.types import RelationType

from .id import ObjectId, ScopeId


@dataclass
class AssociationScopesEntitiesData:
    id: uuid.UUID
    scope_id: ScopeId
    object_id: ObjectId
    relation_type: RelationType
    registered_at: datetime
