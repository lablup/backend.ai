from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionData, SessionEntityData, SessionStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.models.utils import sql_json_merge
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


@dataclass
class SessionStatusBatchUpdater(DataBatchUpdater[SessionRow, SessionEntityData]):
    """Move the named sessions to one status, stamping when it happened.

    ``except_statuses`` leaves the sessions already in one of them alone, so a caller
    that must not disturb, say, a terminal session says which those are.
    """

    session_ids: Sequence[SessionId]
    to_status: SessionStatus
    status_changed_at: datetime
    reason: str | None = None
    except_statuses: Collection[SessionStatus] = ()

    @property
    @override
    def row_class(self) -> type[SessionRow]:
        return SessionRow

    @override
    def conditions(self) -> list[QueryCondition]:
        conditions = [SessionConditions.by_ids(self.session_ids)]
        if self.except_statuses:
            conditions.append(SessionConditions.by_status_not_in(self.except_statuses))
        return conditions

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "status": self.to_status,
            "status_history": sql_json_merge(
                SessionRow.__table__.c.status_history,
                (),
                {self.to_status.name: self.status_changed_at.isoformat()},
            ),
        }
        if self.reason is not None:
            values["status_info"] = self.reason

        if self.to_status == SessionStatus.RUNNING:
            values["starts_at"] = self.status_changed_at
        elif self.to_status == SessionStatus.TERMINATED:
            values["terminated_at"] = self.status_changed_at
        elif self.to_status == SessionStatus.PENDING:
            # Queued afresh: the previous run's start time must not survive.
            values["starts_at"] = None

        return values

    @override
    def to_data(self, row: SessionRow) -> SessionEntityData:
        return row.to_entity_data()
