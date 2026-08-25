from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier


@dataclass(frozen=True)
class RuntimeVariantData(EntityData):
    id: RuntimeVariantID
    name: str
    description: str | None
    reads_vfolder_config_files: bool
    default_model_definition: DefaultModelDefinition
    created_at: datetime
    updated_at: datetime | None

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id
