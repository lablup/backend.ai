from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.vfolder_auto_mount.query_spec import (
    VFolderAutoMountQuerySpec,
)
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow


@dataclass
class VFolderAutoMountSearcher(Searcher[VFolderAutoMountRow, VFolderAutoMountData]):
    """Soft-deleted rows are included; filter on ``deleted_at`` to leave them out."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderAutoMountRow)

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountQuerySpec.own.to_data(row)
