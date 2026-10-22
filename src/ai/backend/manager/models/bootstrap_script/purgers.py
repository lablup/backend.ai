from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.bootstrap_script.searchable_fields import (
    BootstrapScriptSearchableFields,
)
from ai.backend.manager.models.specs.purger import FieldBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck


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
