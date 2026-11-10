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
    created_at: datetime
    deleted_at: datetime | None


@dataclass(frozen=True)
class UserDefaultBootstrapScriptData(FieldData):
    """The script a user's default points at."""

    user_id: UserID
    script_id: BootstrapScriptID


@dataclass(frozen=True)
class BootstrapScriptRevisionData(FieldData):
    """One write of a bootstrap script's content; the latest one is the current content."""

    id: BootstrapScriptRevisionID
    script_id: BootstrapScriptID
    revision_number: int
    script: BootstrapScript
    creator_id: UserID | None
    created_at: datetime
