"""Searcher specs for the bootstrap_script_revisions table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import aliased

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
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
    """Revisions of live scripts that are their owner's default. The scope names the user."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(BootstrapScriptRevisionRow)
            .join(BootstrapScriptRow, BootstrapScriptRow.id == BootstrapScriptRevisionRow.script_id)
            .join(
                UserDefaultBootstrapScriptRow,
                sa.and_(
                    UserDefaultBootstrapScriptRow.script_id == BootstrapScriptRow.id,
                    UserDefaultBootstrapScriptRow.user_id == BootstrapScriptRow.entity_id,
                ),
            )
            .where(BootstrapScriptRow.deleted_at.is_(None))
        )

    @override
    def to_data(self, row: BootstrapScriptRevisionRow) -> BootstrapScriptRevisionData:
        return BootstrapScriptRevisionSearchableFields.own.to_data(row)


@dataclass(kw_only=True)
class CurrentBootstrapScriptRevisionSearcher(
    Searcher[BootstrapScriptRevisionRow, BootstrapScriptRevisionData]
):
    """The latest revision of each named script, which is its current content."""

    script_ids: Sequence[BootstrapScriptID]

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        later = aliased(BootstrapScriptRevisionRow)
        latest_number = (
            sa.select(sa.func.max(later.revision_number))
            .where(later.script_id == BootstrapScriptRevisionRow.script_id)
            .scalar_subquery()
        )
        return sa.select(BootstrapScriptRevisionRow).where(
            BootstrapScriptRevisionRow.script_id.in_(self.script_ids),
            BootstrapScriptRevisionRow.revision_number == latest_number,
        )

    @override
    def to_data(self, row: BootstrapScriptRevisionRow) -> BootstrapScriptRevisionData:
        return BootstrapScriptRevisionSearchableFields.own.to_data(row)
