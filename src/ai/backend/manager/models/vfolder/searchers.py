"""List-read specs for vfolders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.model_card.types import VFolderScanData
from ai.backend.manager.data.vfolder.types import VFolderData, VFolderMountPolicyData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.vfolder.row import VFolderRow, VFolderUserMountPolicyRow
from ai.backend.manager.models.vfolder.searchable_fields import (
    VFolderMountPolicySearchableFields,
    VFolderSearchableFields,
)


@dataclass
class VFolderSearcher(Searcher[VFolderRow, VFolderData]):
    """The vfolder rows a scoped read returns."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderRow)

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return VFolderSearchableFields.own.to_data(row)


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


@dataclass
class VFolderUserMountPolicySearcher(Searcher[VFolderUserMountPolicyRow, VFolderMountPolicyData]):
    """The mount policy rows of one folder."""

    vfolder_id: VFolderUUID = field(kw_only=True)

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderUserMountPolicyRow).where(
            VFolderUserMountPolicyRow.vfolder_id == self.vfolder_id
        )

    @override
    def to_data(self, row: VFolderUserMountPolicyRow) -> VFolderMountPolicyData:
        return VFolderMountPolicySearchableFields.own.to_data(row)
