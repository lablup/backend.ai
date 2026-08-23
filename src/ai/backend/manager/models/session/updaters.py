from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class SessionUpdater(DataUpdater[SessionRow, SessionData]):
    """Rename a session or re-rank it.

    A rename also names every kernel of the session, which the caller carries out
    beside this update.
    """

    session_id: SessionID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    priority: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[SessionRow]:
        return SessionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SessionRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.session_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.priority.update_dict(to_update, "priority")
        return to_update

    @override
    def to_data(self, row: SessionRow) -> SessionData:
        return row.to_dataclass()
