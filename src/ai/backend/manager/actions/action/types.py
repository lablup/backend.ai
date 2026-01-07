from dataclasses import dataclass

from ai.backend.common.data.permission.types import EntityType


@dataclass
class FieldData:
    field_type: EntityType
    field_id: str


@dataclass
class BatchFieldData:
    field_type: EntityType
    field_ids: list[str]
