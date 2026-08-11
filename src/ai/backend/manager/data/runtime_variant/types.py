from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID


@dataclass(frozen=True)
class RuntimeVariantData:
    id: RuntimeVariantID
    name: str
    description: str | None
    reads_vfolder_config_files: bool
    default_model_definition: DefaultModelDefinition
    created_at: datetime
    updated_at: datetime | None
