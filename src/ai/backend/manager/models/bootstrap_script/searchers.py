from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class BootstrapScriptSearcher(Searcher[BootstrapScriptRow, BootstrapScriptData]):
    """Soft-deleted rows are included; filter on ``deleted_at`` to leave them out."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(BootstrapScriptRow)

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return BootstrapScriptSearchableFields.own.to_data(row)
