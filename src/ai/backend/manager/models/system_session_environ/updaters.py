"""DataUpdater implementations for the system session environ repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.errors.system_session_environ import (
    InvalidSystemSessionEnvironKey,
    SystemSessionEnvironDeleted,
    SystemSessionEnvironKeyConflict,
)
from ai.backend.manager.models.specs.types import GuardCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)
from ai.backend.manager.types import OptionalState

__all__ = ("SystemSessionEnvironUpdater",)


@dataclass
class SystemSessionEnvironUpdater(
    GuardedDataUpdater[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    environ_id: SystemSessionEnvironID
    key: OptionalState[str] = field(default_factory=OptionalState[str].nop)

    @property
    @override
    def row_class(self) -> type[SystemSessionEnvironRow]:
        return SystemSessionEnvironRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SystemSessionEnvironRow.id

    @override
    def target_id_value(self) -> SystemSessionEnvironID:
        return self.environ_id

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=SystemSessionEnvironSearchableFields.own.deleted_at.filter.is_null(),
                error=SystemSessionEnvironDeleted(
                    f"System session environ is deleted: {self.environ_id}"
                ),
            ),
        )

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_system_session_environ_key",
                error=SystemSessionEnvironKeyConflict(),
            ),
            IntegrityErrorCheck(
                violation_type=CheckConstraintViolationError,
                constraint_name="ck_system_session_environ_key_is_environ_name",
                error=InvalidSystemSessionEnvironKey(),
            ),
        )

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.key.update_dict(to_update, "key")
        return to_update

    @override
    def to_data(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironData:
        return SystemSessionEnvironSearchableFields.own.to_data(row)
