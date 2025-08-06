from dataclasses import dataclass
from typing import Self

from .types import EntityType, ScopeType


@dataclass
class ScopeId:
    scope_type: ScopeType
    scope_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        scope_type, _, scope_id = val.partition(":")
        return cls(scope_type=ScopeType(scope_type), scope_id=scope_id)

    def to_str(self) -> str:
        return f"{self.scope_type}:{self.scope_id}"


@dataclass
class ObjectId:
    entity_type: EntityType
    entity_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        entity_type, _, entity_id = val.partition(":")
        return cls(entity_type=EntityType(entity_type), entity_id=entity_id)

    def to_str(self) -> str:
        return f"{self.entity_type}:{self.entity_id}"
