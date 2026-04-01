from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RuntimeVariantPresetData:
    id: UUID
    runtime_variant_id: UUID
    name: str
    description: str | None
    rank: int
    preset_target: str
    value_type: str
    default_value: str | None
    key: str
    created_at: datetime
    updated_at: datetime | None
