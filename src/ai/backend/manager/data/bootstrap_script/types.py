from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.bootstrap_script import BootstrapScript, BootstrapScriptID
from ai.backend.common.data.entity.bootstrap_script_revision import BootstrapScriptRevisionID
from ai.backend.common.data.entity.types import FieldData, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID


@dataclass(frozen=True)
class BootstrapScriptData(FieldData):
    id: BootstrapScriptID
    entity: RuntimeEntityID
    is_default: bool
    created_at: datetime
    deleted_at: datetime | None


@dataclass(frozen=True)
class BootstrapScriptRevisionData:
    """One write of a bootstrap script's content; the latest one is the current content."""

    id: BootstrapScriptRevisionID
    script_id: BootstrapScriptID
    revision_number: int
    script: BootstrapScript
    creator_id: UserID | None
    created_at: datetime
