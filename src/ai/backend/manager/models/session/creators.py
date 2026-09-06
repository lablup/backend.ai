"""Insert specs for the sessions table and the rows a session owns."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_dependency import SessionDependencyID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ClusterMode
from ai.backend.manager.data.session.creation import ImageInfo
from ai.backend.manager.data.session.options import SessionStoredOptions
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.data.session.types import (
    SessionDependencyData,
    SessionEntityData,
    SessionStatus,
)
from ai.backend.manager.models.session.row import SessionDependencyRow, SessionRow
from ai.backend.manager.models.specs.creator import EntityCreator, FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = (
    "SessionCreator",
    "SessionDependencyCreator",
)


@dataclass(frozen=True)
class SessionCreator(EntityCreator[SessionRow, SessionEntityData]):
    """Build the session row of an enqueue.

    The session-level snapshot fields are the main kernel's; ``images`` / ``image_ids``
    are deduplicated over the kernels, the main kernel's image first.
    """

    spec: SessionSpec
    image_infos: Mapping[ImageID, ImageInfo]
    enqueue_time: datetime

    @override
    def entity_id(self, row: SessionRow) -> SessionID:
        return SessionID(row.id)

    @override
    def created_in(self, row: SessionRow) -> Collection[EntityIdentifier]:
        return [UserID(row.user_uuid), ProjectID(row.group_id)]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> SessionRow:
        spec = self.spec
        kernel_specs = spec.resource_spec.kernel_specs
        main_kernel = kernel_specs[0] if kernel_specs else None

        session_images: list[str] = []
        session_image_ids: list[UUID] = []
        for kernel in kernel_specs:
            image_id = kernel.execution_spec.resource_input.image_id
            image_info = self.image_infos.get(image_id) if image_id is not None else None
            if image_info is not None:
                session_image_ids.append(image_info.id)
                if image_info.canonical and image_info.canonical not in session_images:
                    if kernel.cluster_role == "main":
                        session_images.insert(0, image_info.canonical)
                    else:
                        session_images.append(image_info.canonical)

        main_mounts = list(main_kernel.vfolder_mounts) if main_kernel else []
        session_requested_starts_at = main_kernel.execution_spec.starts_at if main_kernel else None
        session_batch_timeout = (
            main_kernel.execution_spec.batch_timeout_sec if main_kernel else None
        )
        session_environ = dict(main_kernel.execution_spec.environ) if main_kernel else {}
        session_bootstrap = main_kernel.execution_spec.bootstrap_script if main_kernel else None
        session_startup = main_kernel.execution_spec.startup_command if main_kernel else None

        designated_agent_ids = [
            str(agent) for agent in spec.resource_spec.options.scheduling_target.designated_agents
        ] or None

        cluster_mode_value = (
            spec.resource_spec.options.cluster_mode.value
            if isinstance(spec.resource_spec.options.cluster_mode, ClusterMode)
            else str(spec.resource_spec.options.cluster_mode)
        )

        return SessionRow(
            id=spec.resource_spec.identity.session_id,
            creation_id=spec.resource_spec.identity.creation_id,
            name=spec.resource_spec.identity.session_name,
            access_key=spec.resource_spec.identity.access_key,
            user_uuid=spec.resource_spec.identity.user_uuid,
            group_id=spec.scope.project_id,
            domain_id=spec.scope.domain_id,
            domain_name=str(spec.scope.domain_name),
            resource_group_id=spec.scope.resource_group_id,
            scaling_group_name=str(spec.scope.resource_group_name),
            session_group_id=spec.scope.session_group_id,
            session_type=spec.resource_spec.classification.session_type,
            cluster_mode=cluster_mode_value,
            cluster_size=spec.resource_spec.options.cluster_size,
            priority=spec.resource_spec.options.priority,
            job_priority=spec.resource_spec.options.job_priority,
            is_preemptible=spec.resource_spec.options.is_preemptible,
            status=SessionStatus.PENDING,
            status_history={
                SessionStatus.PENDING.name: self.enqueue_time.isoformat(),
            },
            vfolder_mounts=main_mounts,
            environ=session_environ,
            tag=spec.resource_spec.classification.tag,
            requested_starts_at=session_requested_starts_at,
            batch_timeout=session_batch_timeout,
            callback_url=spec.resource_spec.callback_url,
            images=session_images,
            image_ids=session_image_ids,
            network_type=spec.resource_spec.network.network_type,
            network_id=spec.resource_spec.network.network_id,
            designated_agent_ids=designated_agent_ids,
            options=SessionStoredOptions(
                kernel_groups=spec.resource_spec.options.kernel_groups,
                handler_options=spec.resource_spec.options.handler_options,
                agent_selection_policy=(
                    spec.resource_spec.options.scheduling_target.agent_selection_policy
                ),
            ),
            bootstrap_script=session_bootstrap,
            use_host_network=spec.resource_spec.network.use_host_network,
            timeout=None,
            startup_command=session_startup,
        )

    @override
    def to_data(self, row: SessionRow) -> SessionEntityData:
        return row.to_entity_data()


@dataclass(frozen=True)
class SessionDependencyCreator(
    FieldCreator[SessionID, SessionDependencyRow, SessionDependencyData]
):
    """Record what the session being enqueued waits for."""

    depends_on: SessionID

    @override
    def field_id(self, row: SessionDependencyRow) -> SessionDependencyID:
        return SessionDependencyID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: SessionID) -> SessionDependencyRow:
        return SessionDependencyRow(session_id=owner_id, depends_on=self.depends_on)

    @override
    def to_data(self, row: SessionDependencyRow) -> SessionDependencyData:
        return SessionDependencyData(
            id=SessionDependencyID(row.id),
            session_id=SessionID(row.session_id),
            depends_on=SessionID(row.depends_on),
        )
