"""CreatorSpec implementations for the scheduler enqueue path.

These build :class:`SessionRow` / :class:`KernelRow` from a finalized
:class:`SessionSpec` and plug directly into the RBAC entity creator
executors. Keeping them here (alongside other repository-side creator
specs) lets the scheduler db-source hand them off to
``execute_rbac_entity_creator`` / ``execute_rbac_bulk_entity_creator``
without any retrofit wrapping.

``KernelRowFromSpec`` intentionally omits ``KernelRow.id`` so the DB-
side ``server_default=uuid_generate_v4()`` assigns the kernel primary
key on flush.  ``SessionRowFromSpec`` derives the session-level
aggregates (image list, main-kernel snapshot, requested-slot sum) from
the spec + the pre-fetched :class:`ImageInfo` mapping.

Creators take plain value inputs (``ImageInfo``) instead of ORM
``Row`` objects — the creator's job is to assemble a Row from values,
not to relay data between rows. The db-source converts any upstream
``ImageRow`` query results into ``ImageInfo`` before handing them to
the creators.

Longer term :class:`CreatorSpec` is likely to move down into the model
layer so ``build_row`` stays next to the Row schema it constructs; for
now the base lives under ``repositories/base/creator.py`` and these
creators sit at the repository layer to match.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import ClusterMode, ResourceSlot, ResourceSlotEntry
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.spec import KernelSpec, SessionSpec
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.base.creator import CreatorSpec

__all__ = (
    "KernelRowFromSpec",
    "SessionRowFromSpec",
)


@dataclass(frozen=True)
class KernelRowFromSpec(CreatorSpec[KernelRow]):
    """Build one :class:`KernelRow` from a :class:`KernelSpec`.

    ``image_info`` carries the canonical/architecture/registry strings
    still persisted on ``KernelRow`` alongside ``image_id`` (task #29
    fallback).
    """

    spec: SessionSpec
    kernel_spec: KernelSpec
    image_info: ImageInfo | None
    enqueue_time: datetime

    @override
    def build_row(self) -> KernelRow:
        execution = self.kernel_spec.execution_spec
        image_info = self.image_info
        environ_payload = [f"{k}={v}" for k, v in (execution.environ or {}).items()]
        resource_opts_payload = execution.resource_opts.model_dump(exclude_none=True)
        resolved_mounts = list(self.kernel_spec.vfolder_mounts)
        requested_slots = ResourceSlotEntry.inputs_to_resource_slot(execution.resources)

        return KernelRow(
            session_id=self.spec.identity.session_id,
            session_creation_id=self.spec.identity.creation_id,
            session_name=self.spec.identity.session_name,
            session_type=self.spec.classification.session_type,
            cluster_mode=self.spec.options.cluster_mode.value,
            cluster_size=self.spec.options.cluster_size,
            cluster_role=self.kernel_spec.cluster_role,
            cluster_idx=self.kernel_spec.cluster_idx,
            local_rank=self.kernel_spec.local_rank,
            cluster_hostname=self.kernel_spec.cluster_hostname,
            scaling_group=str(self.spec.scope.resource_group_name),
            domain_name=str(self.spec.scope.domain_name),
            group_id=self.spec.scope.project_id,
            user_uuid=self.spec.identity.user_uuid,
            access_key=self.spec.identity.access_key,
            image=(image_info.canonical if image_info is not None else None),
            image_id=(image_info.id if image_info is not None else None),
            architecture=(image_info.architecture if image_info is not None else None),
            registry=(image_info.registry if image_info is not None else None),
            tag=self.spec.classification.tag,
            starts_at=execution.starts_at,
            status=KernelStatus.PENDING,
            status_history={
                KernelStatus.PENDING.name: self.enqueue_time.isoformat(),
            },
            occupied_slots=ResourceSlot(),
            requested_slots=requested_slots,
            occupied_shares={},
            resource_opts=resource_opts_payload,
            environ=environ_payload,
            bootstrap_script=execution.bootstrap_script,
            startup_command=execution.startup_command,
            internal_data=dict(self.kernel_spec.internal_data),
            callback_url=self.spec.callback_url,
            mounts=[mount.name for mount in resolved_mounts],
            vfolder_mounts=resolved_mounts,
            preopen_ports=list(self.kernel_spec.preopen_ports),
            use_host_network=self.spec.network.use_host_network,
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


@dataclass(frozen=True)
class SessionRowFromSpec(CreatorSpec[SessionRow]):
    """Build one :class:`SessionRow` from a :class:`SessionSpec`.

    Session-level snapshot fields (``vfolder_mounts``, ``environ``,
    ``startup_command``, ``bootstrap_script``, ``starts_at``,
    ``batch_timeout``) are sourced from the main kernel's execution
    spec. ``images`` / ``image_ids`` are deduplicated from each
    kernel's resolved :class:`ImageInfo`, with the main kernel's image
    placed first. ``requested_slots`` aggregates every kernel's
    resource request.
    """

    spec: SessionSpec
    image_infos: Mapping[ImageID, ImageInfo]
    enqueue_time: datetime

    @override
    def build_row(self) -> SessionRow:
        spec = self.spec
        kernel_specs = spec.kernel_specs
        main_kernel = kernel_specs[0] if kernel_specs else None

        session_images: list[str] = []
        session_image_ids: list[UUID] = []
        requested_slots = ResourceSlot()
        for kernel in kernel_specs:
            image_id = kernel.execution_spec.image_id
            image_info = self.image_infos.get(image_id) if image_id is not None else None
            if image_info is not None:
                session_image_ids.append(image_info.id)
                if image_info.canonical and image_info.canonical not in session_images:
                    if kernel.cluster_role == "main":
                        session_images.insert(0, image_info.canonical)
                    else:
                        session_images.append(image_info.canonical)
            requested_slots += ResourceSlotEntry.inputs_to_resource_slot(
                kernel.execution_spec.resources
            )

        main_mounts = list(main_kernel.vfolder_mounts) if main_kernel else []
        session_starts_at = main_kernel.execution_spec.starts_at if main_kernel else None
        session_batch_timeout = (
            main_kernel.execution_spec.batch_timeout_sec if main_kernel else None
        )
        session_environ = dict(main_kernel.execution_spec.environ) if main_kernel else {}
        session_bootstrap = main_kernel.execution_spec.bootstrap_script if main_kernel else None
        session_startup = main_kernel.execution_spec.startup_command if main_kernel else None

        designated_agent_ids = [
            str(agent) for agent in spec.options.scheduling_target.designated_agents
        ] or None

        cluster_mode_value = (
            spec.options.cluster_mode.value
            if isinstance(spec.options.cluster_mode, ClusterMode)
            else str(spec.options.cluster_mode)
        )

        return SessionRow(
            id=spec.identity.session_id,
            creation_id=spec.identity.creation_id,
            name=spec.identity.session_name,
            access_key=spec.identity.access_key,
            user_uuid=spec.identity.user_uuid,
            group_id=spec.scope.project_id,
            domain_id=spec.scope.domain_id,
            domain_name=str(spec.scope.domain_name),
            resource_group_id=spec.scope.resource_group_id,
            scaling_group_name=str(spec.scope.resource_group_name),
            session_type=spec.classification.session_type,
            cluster_mode=cluster_mode_value,
            cluster_size=spec.options.cluster_size,
            priority=spec.options.priority,
            status=SessionStatus.PENDING,
            status_history={
                SessionStatus.PENDING.name: self.enqueue_time.isoformat(),
            },
            requested_slots=requested_slots,
            occupying_slots=ResourceSlot(),
            vfolder_mounts=main_mounts,
            environ=session_environ,
            tag=spec.classification.tag,
            starts_at=session_starts_at,
            batch_timeout=session_batch_timeout,
            callback_url=spec.callback_url,
            images=session_images,
            image_ids=session_image_ids,
            network_type=spec.network.network_type,
            network_id=spec.network.network_id,
            designated_agent_ids=designated_agent_ids,
            bootstrap_script=session_bootstrap,
            use_host_network=spec.network.use_host_network,
            timeout=None,
            startup_command=session_startup,
        )
