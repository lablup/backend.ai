from dataclasses import dataclass
from typing import Self

from ai.backend.common.data.entity.types import EntityType

__all__ = [
    "EntityType",
    "ObjectId",
    "ScopeId",
]


@dataclass(frozen=True)
class ScopeId:
    """Deprecated: use ``EntityIdentifier``; this pair carries the scope id as a string."""

    scope_type: EntityType
    scope_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        scope_type, _, scope_id = val.partition(":")
        return cls(scope_type=EntityType.from_name(scope_type), scope_id=scope_id)

    def to_str(self) -> str:
        return f"{self.scope_type}:{self.scope_id}"


@dataclass(frozen=True)
class ObjectId:
    """Deprecated: read only by the RBAC data migrations, which name an entity as a
    ``(type, id)`` pair. Live code uses ``EntityIdentifier``."""

    entity_type: EntityType
    entity_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        entity_type, _, entity_id = val.partition(":")
        return cls(entity_type=EntityType.from_name(entity_type), entity_id=entity_id)

    def to_str(self) -> str:
        return f"{self.entity_type}:{self.entity_id}"
