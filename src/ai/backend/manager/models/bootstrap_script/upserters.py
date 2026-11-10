from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from asyncpg.exceptions import ForeignKeyViolationError

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.bootstrap_script.types import UserDefaultBootstrapScriptData
from ai.backend.manager.errors.bootstrap_script import BootstrapScriptNotFound
from ai.backend.manager.models.bootstrap_script.row import UserDefaultBootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter


@dataclass
class UserDefaultBootstrapScriptUpserter(
    FieldUpserter[UserID, UserDefaultBootstrapScriptRow, UserDefaultBootstrapScriptData]
):
    """Point the user's default at one script, replacing what stood."""

    script_id: BootstrapScriptID

    @override
    def row_class(self) -> type[UserDefaultBootstrapScriptRow]:
        return UserDefaultBootstrapScriptRow

    @override
    def index_elements(self) -> list[str]:
        return ["user_id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=BootstrapScriptNotFound(f"Bootstrap script {self.script_id} not found"),
            ),
        )

    @override
    def build_insert_values(self, owner_id: UserID) -> dict[str, Any]:
        return {"user_id": owner_id, "script_id": self.script_id}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"script_id": self.script_id}

    @override
    def to_data(self, row: UserDefaultBootstrapScriptRow) -> UserDefaultBootstrapScriptData:
        return BootstrapScriptSearchableFields.user_default.to_data(row)
