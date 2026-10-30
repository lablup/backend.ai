from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.bootstrap_script.types import (
    BootstrapScriptData,
    UserDefaultBootstrapScriptData,
)
from ai.backend.manager.errors.bootstrap_script import DefaultBootstrapScriptPurgeForbidden
from ai.backend.manager.models.bootstrap_script.row import (
    BootstrapScriptRow,
    UserDefaultBootstrapScriptRow,
)
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.specs.purger import FieldBatchPurger, GuardedFieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck, GuardCheck


class UserDefaultBootstrapScriptPurger(
    FieldBatchPurger[UserID, UserDefaultBootstrapScriptRow, UserDefaultBootstrapScriptData]
):
    """Clears the user's default; the script it pointed at stays."""

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(UserDefaultBootstrapScriptRow).where(
            UserDefaultBootstrapScriptRow.user_id == owner_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: UserDefaultBootstrapScriptRow) -> UserDefaultBootstrapScriptData:
        return BootstrapScriptSearchableFields.user_default.to_data(row)


class BootstrapScriptPurger(
    FieldBatchPurger[EntityIdentifier, BootstrapScriptRow, BootstrapScriptData]
):
    @override
    def build_subquery(self, owner_id: EntityIdentifier) -> sa.sql.Select[Any]:
        return sa.select(BootstrapScriptRow).where(
            BootstrapScriptRow.entity_type == owner_id.entity_type(),
            BootstrapScriptRow.entity_id == owner_id,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptSearchableFields.own.to_data(row)


@dataclass
class NonDefaultBootstrapScriptPurger(GuardedFieldPurger[BootstrapScriptRow, BootstrapScriptData]):
    """Removes one bootstrap script that no user's default points at."""

    script_id: BootstrapScriptID

    @override
    def row_class(self) -> type[BootstrapScriptRow]:
        return BootstrapScriptRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return BootstrapScriptRow.id

    @override
    def target_id_value(self) -> BootstrapScriptID:
        return self.script_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=lambda: ~sa.exists().where(
                    UserDefaultBootstrapScriptRow.script_id == BootstrapScriptRow.id
                ),
                error=DefaultBootstrapScriptPurgeForbidden(
                    "Cannot purge the default bootstrap script. Switch the default first."
                ),
            ),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptSearchableFields.own.to_data(row)
