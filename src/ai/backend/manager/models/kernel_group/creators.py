"""Insert specs for the kernel_groups table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel_group import KernelGroupID, KernelGroupRole
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.data.session.options import KernelGroup
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = ("KernelGroupCreator",)


@dataclass(frozen=True)
class KernelGroupCreator(FieldCreator[SessionID, KernelGroupRow, KernelGroupData]):
    """Build one role of the session being enqueued from its resolved group."""

    group: KernelGroup

    @override
    def field_id(self, row: KernelGroupRow) -> KernelGroupID:
        return KernelGroupID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: SessionID) -> KernelGroupRow:
        execution = self.group.execution_spec
        shmem = execution.resource_input.resource_opts.shmem
        return KernelGroupRow(
            session_id=owner_id,
            role=KernelGroupRole(self.group.role),
            image_id=execution.resource_input.image_id,
            shmem=(int(shmem) if shmem is not None else None),
            startup_command=execution.startup_command,
            preopen_ports=list(self.group.preopen_ports),
            requested_starts_at=execution.starts_at,
            batch_timeout_sec=execution.batch_timeout_sec,
        )

    @override
    def to_data(self, row: KernelGroupRow) -> KernelGroupData:
        return KernelGroupData(
            id=KernelGroupID(row.id),
            session_id=row.session_id,
            role=KernelGroupRole(row.role),
            image_id=row.image_id,
            shmem=row.shmem,
            startup_command=row.startup_command,
            preopen_ports=list(row.preopen_ports),
            requested_starts_at=row.requested_starts_at,
            batch_timeout_sec=row.batch_timeout_sec,
        )
