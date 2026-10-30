"""Searcher specs for the bootstrap_script_revisions table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptRevisionData
from ai.backend.manager.models.bootstrap_script.row import (
    BootstrapScriptRow,
    UserDefaultBootstrapScriptRow,
)
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow
from ai.backend.manager.models.bootstrap_script_revision.searchable_fields import (
    BootstrapScriptRevisionSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass(kw_only=True)
class DefaultBootstrapScriptRevisionSearcher(
    Searcher[BootstrapScriptRevisionRow, BootstrapScriptRevisionData]
):
    """Revisions of the live script the user's default points at."""

    user_id: UserID

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(BootstrapScriptRevisionRow)
            .join(BootstrapScriptRow, BootstrapScriptRow.id == BootstrapScriptRevisionRow.script_id)
            .join(
                UserDefaultBootstrapScriptRow,
                UserDefaultBootstrapScriptRow.script_id == BootstrapScriptRow.id,
            )
            .where(
                UserDefaultBootstrapScriptRow.user_id == self.user_id,
                BootstrapScriptRow.deleted_at.is_(None),
            )
        )

    @override
    def to_data(self, row: BootstrapScriptRevisionRow) -> BootstrapScriptRevisionData:
        return BootstrapScriptRevisionSearchableFields.own.to_data(row)
