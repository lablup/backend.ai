"""List-read specs for kernels."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import KernelId
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.kernel_group_vfolder_mount.row import KernelGroupVFolderMountRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KernelSearcher(Searcher[KernelRow, KernelInfo]):
    """The kernel rows a read returns. Which sessions' kernels these are is the
    operation scope's to say."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelRow)

    @override
    def to_data(self, row: KernelRow) -> KernelInfo:
        return row.to_kernel_info()


@dataclass
class LiveKernelsMountingVFolderSearcher(Searcher[KernelRow, KernelId]):
    """The live kernels whose kernel group mounts the vfolder."""

    vfolder_id: VFolderUUID = field(kw_only=True)

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KernelRow).where(
            KernelRow.status.not_in(KernelStatus.terminal_statuses()),
            sa.exists().where(
                KernelGroupVFolderMountRow.kernel_group_id == KernelRow.kernel_group_id,
                KernelGroupVFolderMountRow.vfolder_id == self.vfolder_id,
            ),
        )

    @override
    def to_data(self, row: KernelRow) -> KernelId:
        return KernelId(row.id)
