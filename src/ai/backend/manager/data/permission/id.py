from dataclasses import dataclass
from typing import Self

from ai.backend.common.data.permission.types import EntityType, FieldType, ScopeType


@dataclass(frozen=True)
class FieldRef:
    """
    Represents a reference to a field within an entity.

    A field is a sub-resource that belongs to a parent entity.

    This class combines both the field type and its identifier to form
    a complete reference to a specific field instance.

    Attributes:
        field_type: The type of the field (FieldType enum).
        field_id: The unique identifier of the field.
    """

    field_type: FieldType
    field_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        field_type, _, field_id = val.partition(":")
        return cls(field_type=FieldType(field_type), field_id=field_id)

    def to_str(self) -> str:
        return f"{self.field_type}:{self.field_id}"


@dataclass(frozen=True)
class ScopeId:
    scope_type: ScopeType
    scope_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        scope_type, _, scope_id = val.partition(":")
        return cls(scope_type=ScopeType(scope_type), scope_id=scope_id)

    def to_str(self) -> str:
        return f"{self.scope_type}:{self.scope_id}"


@dataclass(frozen=True)
class ObjectId:
    entity_type: EntityType
    entity_id: str

    @classmethod
    def from_str(cls, val: str) -> Self:
        entity_type, _, entity_id = val.partition(":")
        return cls(entity_type=EntityType(entity_type), entity_id=entity_id)

    def to_str(self) -> str:
        return f"{self.entity_type}:{self.entity_id}"
