"""Single-row read specs for vfolders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.specs.querier import DataQuerier
from ai.backend.manager.models.vfolder.row import VFolderRow


@dataclass
class VFolderQuerier(DataQuerier[VFolderRow, VFolderData]):
    """Reads one vfolder by id."""

    vfolder_id: VFolderUUID

    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return VFolderRow.id

    @override
    def entity_id_value(self) -> VFolderUUID:
        return self.vfolder_id

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return row.to_data()
