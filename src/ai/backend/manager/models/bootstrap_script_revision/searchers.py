"""Searcher specs for the bootstrap_script_revisions table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptRevisionData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow
from ai.backend.manager.models.bootstrap_script_revision.searchable_fields import (
    BootstrapScriptRevisionSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class BootstrapScriptRevisionSearcher(
    Searcher[BootstrapScriptRevisionRow, BootstrapScriptRevisionData]
):
    """Revisions joined to their script, so conditions can name the script's columns."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(BootstrapScriptRevisionRow).join(
            BootstrapScriptRow, BootstrapScriptRow.id == BootstrapScriptRevisionRow.script_id
        )

    @override
    def to_data(self, row: BootstrapScriptRevisionRow) -> BootstrapScriptRevisionData:
        return BootstrapScriptRevisionSearchableFields.own.to_data(row)
