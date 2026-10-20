from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.specs.querier import OwnedFieldQuerier


@dataclass
class BootstrapScriptQuerier(
    OwnedFieldQuerier[EntityIdentifier, BootstrapScriptRow, BootstrapScriptData]
):
    entity_type: EntityType

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(BootstrapScriptRow).where(
            BootstrapScriptRow.entity_type == self.entity_type,
            BootstrapScriptRow.is_default,
        )

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return BootstrapScriptRow.entity_id

    @override
    def to_data(self, row: BootstrapScriptRow) -> BootstrapScriptData:
        return row.to_data()
