"""List-read specs for sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.types import SessionId, VFolderID
from ai.backend.manager.models.session.row import DEAD_SESSION_STATUSES, SessionRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class LiveSessionsMountingVFolderSearcher(Searcher[SessionRow, SessionId]):
    """The live sessions carrying the vfolder among their mounts."""

    vfolder_id: VFolderID = field(kw_only=True)

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(SessionRow).where(
            SessionRow.status.not_in(DEAD_SESSION_STATUSES)
            & SessionRow.vfolder_mounts.contains([{"vfid": str(self.vfolder_id)}])
        )

    @override
    def to_data(self, row: SessionRow) -> SessionId:
        return SessionId(row.id)
