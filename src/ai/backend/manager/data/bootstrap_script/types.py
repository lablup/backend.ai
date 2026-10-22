from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.types import FieldData, RuntimeEntityID


@dataclass(frozen=True)
class BootstrapScriptData(FieldData):
    id: BootstrapScriptID
    entity: RuntimeEntityID
    script: BootstrapScript
    is_default: bool
    created_at: datetime
