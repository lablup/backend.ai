"""Deployment → ``SessionSpecDraft`` assembly.

Lives in ``sokovan/deployment/`` because deployment is the layer that
consumes sessions — deployment types can legitimately depend on
session types, but the reverse would flip the dependency direction
(``data/session/`` importing ``data/deployment/`` types would be
wrong). Every deployment-originated enqueue (route executor,
coordinator-driven re-provision) calls into this builder rather than
rolling its own translation.
"""

from __future__ import annotations

import secrets
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from ai.backend.common.defs.session import SESSION_PRIORITY_DEFAULT
from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.types import (
    MountInfoEntry,
    MountPermission,
    ResourceSlotEntry,
    SessionTypes,
)
from ai.backend.manager.data.deployment.types import DeploymentInfo, ModelRevisionData
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    SchedulingTargetDraft,
    SessionClassificationDraft,
    SessionIdentityDraft,
    SessionNetworkDraft,
    SessionOptionsDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import (
    InternalDataExtras,
    ResourceOpts,
    SessionHandlerOptions,
)
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.deployment import RevisionMissingModelVFolder
from ai.backend.manager.repositories.scheduler.types.session_creation import DeploymentContext


class DeploymentSessionDraftBuilder:
    """Assemble a :class:`SessionSpecDraft` from deployment-originated inputs.

    Single entry point :meth:`build`: route executor passes
    ``(deployment_info, context, route_id, target_revision)`` and
    receives a draft ready for ``SchedulingController.enqueue_session_from_draft``.
    Consolidates the behavior the retired ``SessionCreationSpec.from_deployment_info``
    classmethod used to provide, moved out of the session data layer so
    it no longer imports from ``data/deployment/``.
    """

    @classmethod
    def build(
        cls,
        deployment_info: DeploymentInfo,
        context: DeploymentContext,
        route_id: UUID,
        target_revision: ModelRevisionData,
    ) -> SessionSpecDraft:
        environ = cls._resolve_environ(deployment_info, target_revision, context)
        startup_command = target_revision.execution.startup_command
        mounts = cls._resolve_mounts(target_revision)
        resource_entries = cls._resource_entries(target_revision)
        resource_opts = ResourceOpts.model_validate(
            dict(target_revision.resource_config.resource_opts) or {}
        )
        model_definition_payload = cls._model_definition_payload(target_revision, context)

        if target_revision.model_mount_config.vfolder_id is None:
            raise RevisionMissingModelVFolder(
                f"Revision {target_revision.id} has no model vfolder; cannot build session draft"
            )
        kernel_groups = cls._resolve_kernel_groups(
            cluster_size=target_revision.cluster_config.size,
            execution_spec=KernelExecutionSpecDraft(
                image_id=target_revision.image_id,
                resources=resource_entries,
                resource_opts=resource_opts,
                environ=environ,
                mounts=mounts,
                startup_command=startup_command,
                bootstrap_script=(target_revision.execution.bootstrap_script or None),
            ),
        )

        return SessionSpecDraft(
            identity=SessionIdentityDraft(
                session_id=SessionID(uuid4()),
                creation_id=secrets.token_urlsafe(16),
                session_name=f"{deployment_info.metadata.name}-{route_id!s}",
                access_key=context.session_owner.access_key,
                user_uuid=context.session_owner.uuid,
            ),
            scope=SessionScopeDraft(
                domain_name=DomainName(deployment_info.metadata.domain),
                project_id=ProjectID(context.group_id),
                resource_group_name=ResourceGroupName(deployment_info.metadata.resource_group),
            ),
            classification=SessionClassificationDraft(
                session_type=SessionTypes.INFERENCE,
                tag=deployment_info.metadata.tag,
            ),
            network=SessionNetworkDraft(),
            callback_url=target_revision.execution.callback_url,
            options=SessionOptionsDraft(
                priority=SESSION_PRIORITY_DEFAULT,
                is_preemptible=False,
                cluster_mode=target_revision.cluster_config.mode,
                cluster_size=target_revision.cluster_config.size,
                scheduling_target=SchedulingTargetDraft(),
                kernel_groups=kernel_groups,
                handler_options=SessionHandlerOptions(),
            ),
            internal_data_extras=InternalDataExtras(
                sudo_session_enabled=context.session_owner.sudo_session_enabled,
                model_definition_path=target_revision.model_mount_config.definition_path,
                model_definition=model_definition_payload,
            ),
        )

    @staticmethod
    def _resolve_kernel_groups(
        cluster_size: int,
        execution_spec: KernelExecutionSpecDraft,
    ) -> tuple[KernelGroupDraft, ...]:
        # 1 main + (cluster_size - 1) sub, matching legacy registry Shape (a).
        groups: tuple[KernelGroupDraft, ...] = (
            KernelGroupDraft(
                role=DEFAULT_ROLE,
                replica_count=1,
                execution_spec=execution_spec,
            ),
        )
        if cluster_size > 1:
            groups += (
                KernelGroupDraft(
                    role="sub",
                    replica_count=cluster_size - 1,
                    execution_spec=execution_spec,
                ),
            )
        return groups

    @staticmethod
    def _resolve_environ(
        deployment_info: DeploymentInfo,
        target_revision: ModelRevisionData,
        context: DeploymentContext,
    ) -> dict[str, str]:
        revision_environ = target_revision.model_runtime_config.environ
        environ: dict[str, str] = (
            {k: str(v) for k, v in revision_environ.items()} if revision_environ else {}
        )
        if "BACKEND_MODEL_NAME" not in environ:
            environ["BACKEND_MODEL_NAME"] = deployment_info.metadata.name
        if context.resolved_presets:
            environ.update(context.resolved_presets.environ)
        return environ

    @staticmethod
    def _resolve_mounts(
        target_revision: ModelRevisionData,
    ) -> tuple[MountInfoEntry, ...]:
        # Model vfolder is always first (READ_ONLY), extra mounts follow
        # with their frozen permissions already on each entry.
        if target_revision.model_mount_config.vfolder_id is None:
            raise RevisionMissingModelVFolder(
                f"Revision {target_revision.id} has no model vfolder; cannot build mount entries"
            )
        return (
            MountInfoEntry(
                vfolder_id=target_revision.model_mount_config.vfolder_id,
                mount_destination=(
                    target_revision.model_mount_config.mount_destination or "/models"
                ),
                mount_perm=MountPermission.READ_ONLY,
                subpath=target_revision.model_mount_config.subpath,
            ),
            *target_revision.model_mount_config.extra_mounts,
        )

    @staticmethod
    def _resource_entries(
        target_revision: ModelRevisionData,
    ) -> tuple[ResourceSlotEntry, ...]:
        resource_slots = dict(target_revision.resource_config.resource_slot)
        return tuple(
            ResourceSlotEntry(resource_type=str(k), quantity=str(Decimal(v)))
            for k, v in resource_slots.items()
            if v is not None
        )

    @staticmethod
    def _model_definition_payload(
        target_revision: ModelRevisionData,
        context: DeploymentContext,
    ) -> dict[str, Any] | None:
        """Materialize ``model_definition`` into the kernel payload.

        ``service.start_command`` is taken as-is from the revision snapshot
        (the controller has already resolved any ``{model_path}`` placeholder
        against ``models[0].model_path`` at revision creation time). Preset
        ARGS are appended as separate argv tokens via
        :meth:`ModelDefinition.with_args_appended` so the merge stays on
        typed objects up to the final ``model_dump``.
        """
        model_definition = target_revision.model_definition
        if model_definition is None:
            return None
        args = (context.resolved_presets.args if context.resolved_presets else None) or []
        if args:
            model_definition = model_definition.with_args_appended(args)
        return model_definition.model_dump(mode="json")
