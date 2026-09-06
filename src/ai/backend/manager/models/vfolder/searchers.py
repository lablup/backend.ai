"""List-read specs for vfolders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.data.model_card.types import VFolderScanData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.vfolder.row import VFolderRow


@dataclass
class VFolderScanTargetSearcher(Searcher[VFolderRow, VFolderScanData]):
    """The live model folders a model-store scan walks.

    The project is the scan's own, not read off the row: the search is bounded to
    it, so a row can only be one of that project's.
    """

    project_id: ProjectID = field(kw_only=True)

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderRow)

    @override
    def to_data(self, row: VFolderRow) -> VFolderScanData:
        return VFolderScanData(
            id=row.id,
            name=row.name,
            host=row.host,
            quota_scope_id=row.quota_scope_id,
            unmanaged_path=row.unmanaged_path,
            domain_name=row.domain_name,
            project_id=self.project_id,
        )
