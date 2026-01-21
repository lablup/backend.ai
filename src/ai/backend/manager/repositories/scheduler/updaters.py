"""BatchUpdater specs for scheduler repository operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, override

from dateutil.tz import tzutc

from ai.backend.manager.models.session import SessionRow, SessionStatus
from ai.backend.manager.models.utils import sql_json_merge
from ai.backend.manager.repositories.base.updater import BatchUpdaterSpec


@dataclass
class SessionStatusBatchUpdaterSpec(BatchUpdaterSpec[SessionRow]):
    """BatchUpdaterSpec for batch updating session status.

    Only specifies what values to update. The target sessions are determined
    by conditions passed to BatchUpdater separately.
    """

    to_status: SessionStatus
    reason: Optional[str] = None

    @property
    @override
    def row_class(self) -> type[SessionRow]:
        return SessionRow

    @override
    def build_values(self) -> dict[str, Any]:
        now = datetime.now(tzutc())
        values: dict[str, Any] = {
            "status": self.to_status,
            "status_history": sql_json_merge(
                SessionRow.__table__.c.status_history,
                (),
                {self.to_status.name: now.isoformat()},
            ),
        }
        if self.reason is not None:
            values["status_info"] = self.reason

        if self.to_status == SessionStatus.RUNNING:
            values["starts_at"] = now
        elif self.to_status == SessionStatus.TERMINATED:
            values["terminated_at"] = now

        return values
