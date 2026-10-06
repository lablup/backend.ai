"""Insert specs for the kernels table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import ResourceSlot, ResourceSlotEntry
from ai.backend.manager.data.kernel.types import KernelInfo, KernelStatus
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.spec import KernelSpec, SessionSpec
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = ("KernelCreator",)


@dataclass(frozen=True)
class KernelCreator(FieldCreator[SessionID, KernelRow, KernelInfo]):
    """Build one kernel of the session being enqueued.

    ``image_info`` carries the canonical/architecture/registry strings still persisted
    on the row beside ``image_id``. The row's id is left to the database.
    """

    spec: SessionSpec
    kernel_spec: KernelSpec
    image_info: ImageInfo | None
    enqueue_time: datetime

    def requested_slots(self) -> ResourceSlot:
        return ResourceSlotEntry.inputs_to_resource_slot(
            self.kernel_spec.execution_spec.resource_input.resources
        )

    @override
    def field_id(self, row: KernelRow) -> KernelID:
        return KernelID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: SessionID) -> KernelRow:
        execution = self.kernel_spec.execution_spec
        image_info = self.image_info
        environ_payload = [f"{k}={v}" for k, v in (execution.environ or {}).items()]
        resource_opts_payload = execution.resource_input.resource_opts.model_dump(exclude_none=True)
        resolved_mounts = list(self.kernel_spec.vfolder_mounts)

        return KernelRow(
            session_id=owner_id,
            session_creation_id=self.spec.resource_spec.identity.creation_id,
            session_name=self.spec.resource_spec.identity.session_name,
            session_type=self.spec.resource_spec.classification.session_type,
            cluster_mode=self.spec.resource_spec.options.cluster_mode.value,
            cluster_size=self.spec.resource_spec.options.cluster_size,
            cluster_role=self.kernel_spec.cluster_role,
            cluster_idx=self.kernel_spec.cluster_idx,
            local_rank=self.kernel_spec.local_rank,
            cluster_hostname=self.kernel_spec.cluster_hostname,
            scaling_group=str(self.spec.scope.resource_group_name),
            resource_group_id=self.spec.scope.resource_group_id,
            domain_name=str(self.spec.scope.domain_name),
            group_id=self.spec.scope.project_id,
            user_uuid=self.spec.resource_spec.identity.user_uuid,
            access_key=self.spec.resource_spec.identity.access_key,
            image=(image_info.canonical if image_info is not None else None),
            image_id=(image_info.id if image_info is not None else None),
            architecture=(image_info.architecture if image_info is not None else None),
            registry=(image_info.registry if image_info is not None else None),
            tag=self.spec.resource_spec.classification.tag,
            starts_at=execution.starts_at,
            status=KernelStatus.PENDING,
            status_history={
                KernelStatus.PENDING.name: self.enqueue_time.isoformat(),
            },
            occupied_shares={},
            resource_opts=resource_opts_payload,
            environ=environ_payload,
            bootstrap_script=execution.bootstrap_script,
            startup_command=execution.startup_command,
            internal_data=dict(self.kernel_spec.internal_data),
            callback_url=self.spec.resource_spec.callback_url,
            mounts=[mount.name for mount in resolved_mounts],
            vfolder_mounts=resolved_mounts,
            preopen_ports=list(self.kernel_spec.preopen_ports),
            use_host_network=self.spec.resource_spec.network.use_host_network,
            uid=self.kernel_spec.uid,
            main_gid=self.kernel_spec.main_gid,
            gids=list(self.kernel_spec.supplementary_gids),
            # Port columns are NOT NULL on KernelRow; legacy enqueue
            # initialises them to 0 and the agent fills in the real
            # values once the container lands.
            repl_in_port=0,
            repl_out_port=0,
            stdin_port=0,
            stdout_port=0,
        )

    @override
    def to_data(self, row: KernelRow) -> KernelInfo:
        return row.to_kernel_info()
