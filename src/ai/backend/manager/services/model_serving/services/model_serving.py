from __future__ import annotations

import logging
import secrets
import uuid
from collections.abc import Sequence
from http import HTTPStatus
from typing import Any, cast

import aiohttp
from pydantic import HttpUrl
from yarl import URL

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.contexts.user import current_user
from ai.backend.common.defs.session import SESSION_PRIORITY_DEFAULT
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
)
from ai.backend.common.events.event_types.kernel.types import (
    KernelLifecycleEventReason,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.hub import EventHub
from ai.backend.common.events.hub.propagators.bypass import AsyncBypassPropagator
from ai.backend.common.events.types import EventDomain
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import (
    AccessKey,
    MountInfoEntry,
    MountPermission,
    ResourceSlotEntry,
    SessionTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ImageIdentifierDraft,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    MountMetadata,
    ResourceSpecDraft,
    RevisionDraft,
    RouteHealthStatus,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.model_serving.types import (
    CompactServiceInfo,
    ErrorInfo,
    RouteInfo,
    ServiceInfo,
)
from ai.backend.manager.data.model_serving.types import (
    EndpointTokenData as ServiceEndpointTokenData,
)
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
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.errors.resource import RuntimeVariantNotFound
from ai.backend.manager.errors.service import (
    EndpointAccessForbiddenError,
    EndpointNotFound,
    ModelServiceNotFound,
    RouteNotFound,
)
from ai.backend.manager.models.endpoint import EndpointLifecycle
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.model_serving.creators import EndpointTokenCreatorSpec
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.model_serving.updaters import EndpointUpdaterSpec
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.model_serving.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_model_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.delete_route import (
    DeleteRouteAction,
    DeleteRouteActionResult,
)
from ai.backend.manager.services.model_serving.actions.dry_run_model_service import (
    DryRunModelServiceAction,
    DryRunModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.force_sync import (
    ForceSyncAction,
    ForceSyncActionResult,
)
from ai.backend.manager.services.model_serving.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_serving.actions.get_model_service_info import (
    GetModelServiceInfoAction,
    GetModelServiceInfoActionResult,
)
from ai.backend.manager.services.model_serving.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_serving.actions.list_model_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.actions.modify_endpoint import (
    ModifyEndpointAction,
    ModifyEndpointActionResult,
)
from ai.backend.manager.services.model_serving.actions.search_services import (
    SearchServicesAction,
    SearchServicesActionResult,
)
from ai.backend.manager.services.model_serving.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_serving.actions.validate_model_service import (
    ValidateModelServiceAction,
    ValidateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.services.utils import validate_endpoint_access
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import MountOptionModel

log = BraceStyleAdapter(logging.getLogger(__name__))


class ModelServingService:
    _agent_registry: AgentRegistry
    _background_task_manager: BackgroundTaskManager
    _event_dispatcher: EventDispatcher
    _event_hub: EventHub
    _storage_manager: StorageSessionManager
    _config_provider: ManagerConfigProvider
    _repository: ModelServingRepository
    _deployment_repository: DeploymentRepository
    _runtime_variant_repository: RuntimeVariantRepository
    _scheduler_repository: SchedulerRepository

    _valkey_live: ValkeyLiveClient
    _deployment_controller: DeploymentController
    _scheduling_controller: SchedulingController
    _route_controller: RouteController

    def __init__(
        self,
        agent_registry: AgentRegistry,
        background_task_manager: BackgroundTaskManager,
        event_dispatcher: EventDispatcher,
        event_hub: EventHub,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
        valkey_live: ValkeyLiveClient,
        repository: ModelServingRepository,
        deployment_repository: DeploymentRepository,
        runtime_variant_repository: RuntimeVariantRepository,
        scheduler_repository: SchedulerRepository,
        deployment_controller: DeploymentController,
        scheduling_controller: SchedulingController,
        route_controller: RouteController,
    ) -> None:
        self._agent_registry = agent_registry
        self._background_task_manager = background_task_manager
        self._event_dispatcher = event_dispatcher
        self._event_hub = event_hub
        self._storage_manager = storage_manager
        self._config_provider = config_provider
        self._valkey_live = valkey_live
        self._repository = repository
        self._deployment_repository = deployment_repository
        self._runtime_variant_repository = runtime_variant_repository
        self._scheduler_repository = scheduler_repository
        self._deployment_controller = deployment_controller
        self._scheduling_controller = scheduling_controller
        self._route_controller = route_controller
        # Map SessionStatus to legacy event names for backward compatibility
        self._status_to_event_name: dict[SessionStatus, str] = {
            SessionStatus.PENDING: "session_enqueued",
            SessionStatus.SCHEDULED: "session_scheduled",
            SessionStatus.PREPARING: "session_preparing",
            SessionStatus.PULLING: "session_preparing",
            SessionStatus.PREPARED: "session_prepared",
            SessionStatus.CREATING: "session_creating",
            SessionStatus.RUNNING: "session_started",
            SessionStatus.TERMINATING: "session_terminating",
            SessionStatus.TERMINATED: "session_terminated",
            SessionStatus.CANCELLED: "session_cancelled",
            SessionStatus.ERROR: "session_cancelled",
        }

    async def _generate_revision(
        self,
        draft: ModelRevisionSpecDraft,
        resource_group: str,
    ) -> ModelRevisionSpec:
        """Resolve a final ModelRevisionSpec via DeploymentController's unified merge pipeline."""
        return await self._deployment_controller.resolve_legacy_revision_spec(
            draft_revision=draft,
            resource_group=resource_group,
        )

    async def _check_model_vfolder_ownership_type(self, vfolder_id: uuid.UUID) -> None:
        """Check model vfolder ownership type."""
        vfolder_ownership_type = await self._repository.get_vfolder_ownership_type(vfolder_id)
        if vfolder_ownership_type == VFolderOwnershipType.GROUP:
            raise InvalidAPIParameters("Cannot use project-type vfolder for model service")

    @staticmethod
    def _build_dry_run_mount_entries(
        model_vfolder_id: uuid.UUID,
        model_mount_destination: str,
        extra_mounts: Sequence[Any],
    ) -> tuple[MountInfoEntry, ...]:
        """Assemble the dry-run session mount list: model vfolder (READ_ONLY)
        followed by each caller-supplied extra mount with its frozen
        permission and resolved kernel path.
        """
        entries: list[MountInfoEntry] = [
            MountInfoEntry(
                vfolder_id=VFolderUUID(model_vfolder_id),
                mount_destination=model_mount_destination,
                mount_perm=MountPermission.READ_ONLY,
            )
        ]
        for m in extra_mounts:
            entries.append(
                MountInfoEntry(
                    vfolder_id=VFolderUUID(m.vfid.folder_id),
                    mount_destination=str(m.kernel_path),
                    mount_perm=m.mount_perm,
                )
            )
        return tuple(entries)

    @staticmethod
    def _resource_entries_from_config(
        resources: dict[str, str | int | float] | None,
    ) -> tuple[ResourceSlotEntry, ...]:
        """Project the dry-run ``ServiceConfig.resources`` dict into the
        typed :class:`ResourceSlotEntry` list the draft expects.
        """
        if not resources:
            return ()
        return tuple(
            ResourceSlotEntry(resource_type=str(k), quantity=str(v)) for k, v in resources.items()
        )

    async def list_serve(self, action: ListModelServiceAction) -> ListModelServiceActionResult:
        endpoints = await self._repository.list_endpoints_by_owner_validated(
            action.session_owener_id, name=action.name
        )

        return ListModelServiceActionResult(
            data=[
                CompactServiceInfo(
                    id=endpoint.id,
                    name=endpoint.name,
                    replicas=endpoint.replicas,
                    desired_session_count=endpoint.replicas,
                    active_route_count=len([
                        r
                        for r in endpoint.routings
                        if r.status == RouteStatus.RUNNING
                        and r.health_status == RouteHealthStatus.HEALTHY
                    ])
                    if endpoint.routings
                    else 0,
                    service_endpoint=HttpUrl(endpoint.url) if endpoint.url else None,
                    is_public=endpoint.open_to_public,
                )
                for endpoint in endpoints
            ],
        )

    async def search_services(self, action: SearchServicesAction) -> SearchServicesActionResult:
        querier = BatchQuerier(
            pagination=OffsetPagination(offset=action.offset, limit=action.limit),
            conditions=action.conditions,
        )
        result = await self._repository.search_services_paginated(action.session_owner_id, querier)
        return SearchServicesActionResult(
            items=result.items,
            total_count=result.total_count,
            offset=action.offset,
            limit=action.limit,
        )

    async def check_user_access(self) -> None:
        user_data = current_user()
        if user_data is None or user_data.is_authorized is False:
            raise GenericForbidden("Only authorized requests may have access key scopes.")

    async def delete(self, action: DeleteModelServiceAction) -> DeleteModelServiceActionResult:
        service_id = action.service_id

        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(service_id)
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Get endpoint data
        endpoint_data = await self._repository.get_endpoint_by_id(service_id)
        if not endpoint_data:
            raise ModelServiceNotFound

        # Determine lifecycle stage based on routes
        has_routes = endpoint_data.routings and len(endpoint_data.routings) > 0
        if has_routes:
            lifecycle_stage = EndpointLifecycle.DESTROYING
            replicas = 0
        else:
            lifecycle_stage = EndpointLifecycle.DESTROYED
            replicas = None

        # Update endpoint lifecycle
        await self._repository.update_endpoint_lifecycle(service_id, lifecycle_stage, replicas)

        return DeleteModelServiceActionResult(service_id=service_id)

    async def dry_run(self, action: DryRunModelServiceAction) -> DryRunModelServiceActionResult:
        # TODO: Seperate background task definition and trigger into different layer
        service_prepare_ctx = action.model_service_prepare_ctx

        model_vfolder_id = service_prepare_ctx.model_vfolder_id
        await self._check_model_vfolder_ownership_type(model_vfolder_id)

        # Legacy path carries the runtime variant as a name; internal
        # revision drafts now key on ``runtime_variant_id``, so resolve the
        # name into the typed id at this single service entry point.
        variant = await self._runtime_variant_repository.get_by_name(str(action.runtime_variant))
        runtime_variant_id = RuntimeVariantID(variant.id)

        # Use RevisionGenerator to load service definition and merge with API request
        revision_draft = ModelRevisionSpecDraft(
            image_identifier=ImageIdentifierDraft(
                canonical=action.image,
                architecture=action.architecture,
            ),
            resource_spec=ResourceSpecDraft(
                cluster_mode=action.cluster_mode,
                cluster_size=action.cluster_size,
                resource_slots=action.config.resources,
                resource_opts=action.config.resource_opts,
            ),
            mounts=MountMetadata(
                model_vfolder_id=model_vfolder_id,
                model_definition_path=None,
                model_mount_destination=action.config.model_mount_destination,
                model_mount_perm=MountPermission.READ_ONLY,
                extra_mounts=[
                    MountInfoEntry(
                        vfolder_id=VFolderUUID(m.vfid.folder_id),
                        mount_destination=m.kernel_path.as_posix(),
                        mount_perm=m.mount_perm,
                    )
                    for m in service_prepare_ctx.extra_mounts
                ],
            ),
            execution=ExecutionSpec(
                runtime_variant_id=runtime_variant_id,
                startup_command=action.startup_command,
                environ=action.config.environ,
            ),
        )
        revision = await self._generate_revision(revision_draft, service_prepare_ctx.scaling_group)
        image_data = await self._repository.get_image_by_id(revision.image_id)
        action = action.with_revision(
            revision,
            image=image_data.name,
            architecture=image_data.architecture,
        )

        # Get user with keypair
        created_user = await self._repository.get_user_with_keypair(action.request_user_id)
        if not created_user:
            raise InvalidAPIParameters("User not found")

        sudo_session_enabled = action.sudo_session_enabled

        # Build the draft inline — no SessionCreationSpec detour, no
        # per-kernel ``creation_config`` dict shuffling. The single
        # kernel group is replicated by ``ExpandKernelGroupsRule`` into
        # ``cluster_size`` per-replica specs.
        session_creation_id = secrets.token_urlsafe(16)
        session_name = f"model-eval-{session_creation_id}"

        mount_entries = self._build_dry_run_mount_entries(
            model_vfolder_id,
            action.config.model_mount_destination,
            service_prepare_ctx.extra_mounts,
        )
        resource_entries = self._resource_entries_from_config(action.config.resources)
        resource_opts = ResourceOpts.model_validate(action.config.resource_opts or {})
        environ = dict(action.config.environ or {})
        callback_url = URL(action.callback_url.unicode_string()) if action.callback_url else None
        kernel_groups = await self._resolve_kernel_groups(
            cluster_size=action.cluster_size,
            execution_spec=KernelExecutionSpecDraft(
                image_id=ImageID(image_data.id),
                resources=resource_entries,
                resource_opts=resource_opts,
                environ=environ,
                mounts=mount_entries,
                startup_command=action.startup_command,
                bootstrap_script=action.bootstrap_script or None,
            ),
        )

        domain_name = DomainName(action.domain_name)
        domain_id = await self._scheduler_repository.get_domain_id_by_name(domain_name)
        if service_prepare_ctx.scaling_group:
            resource_group_name = ResourceGroupName(service_prepare_ctx.scaling_group)
            resource_group_id = await self._scheduler_repository.get_resource_group_id_by_name(
                resource_group_name
            )
            session_scope = SessionScopeDraft(
                domain_id=domain_id,
                domain_name=domain_name,
                project_id=ProjectID(service_prepare_ctx.group_id),
                resource_group_id=resource_group_id,
                resource_group_name=resource_group_name,
            )
        else:
            resource_group = await self._scheduler_repository.pick_default_resource_group(
                access_key=AccessKey(service_prepare_ctx.owner_access_key),
                domain_name=action.domain_name,
                project_id=ProjectID(service_prepare_ctx.group_id),
            )
            session_scope = SessionScopeDraft(
                domain_id=domain_id,
                domain_name=domain_name,
                project_id=ProjectID(service_prepare_ctx.group_id),
                resource_group_id=resource_group.id,
                resource_group_name=resource_group.name,
            )

        draft = SessionSpecDraft(
            identity=SessionIdentityDraft(
                session_id=SessionID(uuid.uuid4()),
                creation_id=session_creation_id,
                session_name=session_name,
                access_key=AccessKey(service_prepare_ctx.owner_access_key),
                user_uuid=created_user.uuid,
            ),
            scope=session_scope,
            classification=SessionClassificationDraft(
                session_type=SessionTypes.INFERENCE,
                tag=action.tag,
            ),
            network=SessionNetworkDraft(),
            callback_url=callback_url,
            options=SessionOptionsDraft(
                priority=SESSION_PRIORITY_DEFAULT,
                is_preemptible=False,
                cluster_mode=action.cluster_mode,
                cluster_size=action.cluster_size,
                scheduling_target=SchedulingTargetDraft(),
                kernel_groups=kernel_groups,
                handler_options=SessionHandlerOptions(),
            ),
            internal_data_extras=InternalDataExtras(
                sudo_session_enabled=sudo_session_enabled,
                model_definition_path=service_prepare_ctx.model_definition_path,
            ),
        )

        # Dry-run path: the agent falls back to reading the
        # ``model_definition_path`` from the mounted model vfolder since
        # no pre-resolved ``model_definition`` overlay exists here.
        session_id = await self._scheduling_controller.enqueue_session_from_draft(draft)
        session_id_str = str(session_id)

        async def _task(reporter: ProgressReporter) -> None:
            # Use AsyncBypassPropagator to receive SchedulingBroadcastEvent
            propagator = AsyncBypassPropagator()
            try:
                self._event_hub.register_event_propagator(
                    propagator, aliases=[(EventDomain.SESSION, session_id_str)]
                )

                async for event in propagator.receive():
                    if isinstance(event, SchedulingBroadcastEvent):
                        status = SessionStatus(event.status_transition)
                        # Convert status to legacy event name for backward compatibility
                        event_name = self._status_to_event_name.get(status, event.status_transition)
                        task_message = {
                            "event": event_name,
                            "session_id": str(event.session_id),
                        }
                        await reporter.update(message=dump_json_str(task_message))

                        # When session becomes RUNNING, mark for termination and exit
                        if status == SessionStatus.RUNNING:
                            await self._scheduling_controller.mark_sessions_for_termination(
                                [session_id],
                                reason="DRY_RUN_COMPLETE",
                            )

                        # Exit loop on terminal states
                        if status.is_terminal():
                            break
            finally:
                self._event_hub.unregister_event_propagator(propagator.id())

        task_id = await self._background_task_manager.start(_task)
        return DryRunModelServiceActionResult(task_id)

    async def _resolve_kernel_groups(
        self,
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

    async def get_model_service_info(
        self, action: GetModelServiceInfoAction
    ) -> GetModelServiceInfoActionResult:
        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Get endpoint data
        endpoint_data = await self._repository.get_endpoint_by_id(action.service_id)
        if not endpoint_data:
            raise ModelServiceNotFound
        if endpoint_data.runtime_variant_id is None:
            raise RuntimeVariantNotFound()

        return GetModelServiceInfoActionResult(
            ServiceInfo(
                deployment_id=DeploymentID(endpoint_data.id),
                model_vfolder_id=VFolderUUID(endpoint_data.model),
                extra_mounts=[m.vfolder_id for m in endpoint_data.extra_mounts],
                name=endpoint_data.name,
                model_definition_path=endpoint_data.model_definition_path,
                replicas=endpoint_data.replicas,
                desired_session_count=endpoint_data.replicas,
                active_routes=[
                    RouteInfo(
                        route_id=r.id,
                        session_id=r.session,
                        traffic_ratio=r.traffic_ratio,
                    )
                    for r in endpoint_data.routings
                ]
                if endpoint_data.routings
                else [],
                service_endpoint=HttpUrl(endpoint_data.url) if endpoint_data.url else None,
                is_public=endpoint_data.open_to_public,
                runtime_variant_id=endpoint_data.runtime_variant_id,
            )
        )

    async def list_errors(self, action: ListErrorsAction) -> ListErrorsActionResult:
        # Get endpoint
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Get endpoint data
        endpoint_data = await self._repository.get_endpoint_by_id(action.service_id)
        if not endpoint_data:
            raise ModelServiceNotFound

        error_routes = (
            [r for r in endpoint_data.routings if r.status == RouteStatus.FAILED_TO_START]
            if endpoint_data.routings
            else []
        )

        return ListErrorsActionResult(
            error_info=[
                ErrorInfo(
                    session_id=route.error_data.get("session_id"), error=route.error_data["errors"]
                )
                for route in error_routes
            ],
            retries=endpoint_data.retries,
        )

    async def clear_error(self, action: ClearErrorAction) -> ClearErrorActionResult:
        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Clear errors
        success = await self._repository.clear_endpoint_errors(action.service_id)

        if not success:
            raise ModelServiceNotFound

        return ClearErrorActionResult(success=True)

    async def update_route(self, action: UpdateRouteAction) -> UpdateRouteActionResult:
        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Update route traffic
        updated_endpoint_data = await self._repository.update_route_traffic(
            self._valkey_live, action.route_id, action.service_id, action.traffic_ratio
        )
        if not updated_endpoint_data:
            raise ModelServiceNotFound

        # AppProxy push happens out-of-band: hint the route coordinator
        # to resync at its next short cycle instead of issuing a
        # synchronous call from the API path.
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.APPPROXY_SYNC)

        return UpdateRouteActionResult(route_id=action.route_id)

    async def delete_route(self, action: DeleteRouteAction) -> DeleteRouteActionResult:
        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Get route
        route_data = await self._repository.get_route_by_id(action.route_id, action.service_id)

        if not route_data:
            raise RouteNotFound

        if route_data.status == RouteStatus.PROVISIONING:
            raise InvalidAPIParameters("Cannot remove route in PROVISIONING status")

        # Get session for destruction
        route_row = await self._repository.get_route_with_session(action.route_id)
        if not route_row:
            raise RouteNotFound

        if route_row.session_row:
            await self._scheduling_controller.mark_sessions_for_termination(
                [route_row.session_row.id],
                reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN.value,
                forced=False,
            )

        # Decrease endpoint replicas
        await self._repository.decrease_endpoint_replicas(action.service_id)

        return DeleteRouteActionResult(route_id=action.route_id)

    async def generate_token(self, action: GenerateTokenAction) -> GenerateTokenActionResult:
        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        # Get endpoint data
        endpoint_data = await self._repository.get_endpoint_by_id(action.service_id)
        if not endpoint_data:
            raise ModelServiceNotFound

        # Get scaling group info
        scaling_group_data = await self._repository.get_scaling_group_info(
            endpoint_data.resource_group
        )
        if not scaling_group_data:
            raise InvalidAPIParameters(f"Scaling group {endpoint_data.resource_group} not found")

        # Generate token via wsproxy
        body = {"user_uuid": str(endpoint_data.session_owner_id), "exp": action.expires_at}
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{scaling_group_data.wsproxy_addr}/v2/endpoints/{endpoint_data.id}/token",
                json=body,
                headers={
                    "accept": "application/json",
                    "X-BackendAI-Token": scaling_group_data.wsproxy_api_token,
                },
            ) as resp,
        ):
            resp_json = await resp.json()
            if resp.status != HTTPStatus.OK:
                raise EndpointNotFound(
                    f"Failed to generate token: {resp.status} {resp.reason} {resp_json}"
                )
            token = resp_json["token"]

        # Create token in database
        token_id = uuid.uuid4()
        token_creator = Creator(
            spec=EndpointTokenCreatorSpec(
                id=token_id,
                token=token,
                endpoint=DeploymentID(endpoint_data.id),
                domain=endpoint_data.domain,
                project=endpoint_data.project,
                session_owner=endpoint_data.session_owner_id,
            )
        )

        # Access already validated above, just create the token
        token_data = await self._repository.create_endpoint_token(token_creator)
        if not token_data:
            raise ModelServiceNotFound

        # Convert data types
        service_token_data = ServiceEndpointTokenData(
            id=token_data.id,
            token=token_data.token,
            endpoint=token_data.endpoint,
            session_owner=token_data.session_owner,
            domain=token_data.domain,
            project=token_data.project,
            created_at=token_data.created_at,
        )
        return GenerateTokenActionResult(data=service_token_data)

    async def force_sync_with_app_proxy(self, action: ForceSyncAction) -> ForceSyncActionResult:
        # Validate access
        await self.check_user_access()
        validation_data = await self._repository.get_endpoint_access_validation_data(
            action.service_id
        )
        if not validation_data:
            raise ModelServiceNotFound
        if not validate_endpoint_access(validation_data):
            raise EndpointAccessForbiddenError

        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.APPPROXY_SYNC)

        return ForceSyncActionResult(success=True)

    async def modify_endpoint(self, action: ModifyEndpointAction) -> ModifyEndpointActionResult:
        spec = cast(EndpointUpdaterSpec, action.updater.spec)

        # 1. Apply endpoint-level changes (name, resource_group, replicas)
        #    via the existing repository method (which only writes endpoint columns).
        result = await self._repository.modify_endpoint_fields(
            action.deployment_id,
            action.updater,
            self._agent_registry,
            self._config_provider.legacy_etcd_config_loader,
        )

        # 2. If revision-level fields changed, create + activate a new revision.
        #    Revisions are immutable, so every mutation goes through the same
        #    ``add_revision`` entry point as fresh creation — this legacy path
        #    merely supplies the latest revision as the caller-provided base
        #    so that untouched fields survive while yaml stays authoritative.
        #    The latest (rather than current/active) revision is used so that
        #    a modify issued while a previous revision is still deploying
        #    layers on top of that in-flight revision instead of discarding
        #    its changes.
        if spec.has_revision_changes():
            latest_rev = await self._deployment_repository.get_latest_revision(action.deployment_id)
            latest_draft = latest_rev.to_draft()
            if latest_draft.mounts is None:
                raise InvalidAPIParameters("model vfolder id is missing on the latest revision")
            override_draft = await self._build_revision_overrides_from_spec(spec)
            definition_path_override = spec.model_definition_path.optional_value()
            draft_with_definition_path_override = RevisionDraft(
                mounts=MountMetadata(
                    model_vfolder_id=latest_draft.mounts.model_vfolder_id,
                    model_definition_path=definition_path_override,
                    model_mount_destination=latest_draft.mounts.model_mount_destination,
                    extra_mounts=list(latest_draft.mounts.extra_mounts),
                    model_mount_perm=latest_draft.mounts.model_mount_perm,
                    vfolder_subpath=latest_draft.mounts.vfolder_subpath,
                )
            )
            override_draft = override_draft.merge(draft_with_definition_path_override)
            # Legacy ``ModifyEndpoint`` semantics preserve untouched fields by
            # layering overrides on top of the existing revision. The
            # controller's ``add_revision`` no longer accepts a caller-provided
            # ``base`` layer, so we pre-merge here and pass the result as the
            # request-level override draft.
            overrides = latest_draft.merge(override_draft)

            revision = await self._deployment_controller.add_revision(
                endpoint_id=action.deployment_id,
                overrides=overrides,
            )
            await self._deployment_controller.activate_revision(action.deployment_id, revision.id)
        elif spec.replica_count_modified():
            # Replica-only change: trigger CHECK_REPLICA to reconcile
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.CHECK_REPLICA,
            )

        return ModifyEndpointActionResult(
            deployment_id=action.deployment_id, success=result.success, data=result.data
        )

    async def _build_revision_overrides_from_spec(
        self,
        spec: EndpointUpdaterSpec,
    ) -> RevisionDraft:
        """Convert ``EndpointUpdaterSpec`` overrides into a ``RevisionDraft``.

        Only fields the user explicitly modified are populated. Fields left
        untouched stay ``None`` so that the controller's merge pipeline can
        fall through to (in priority order) the current revision base,
        deployment-config.yaml, preset, and model-definition.yaml.
        Image ref → image_id resolution happens here because legacy specs
        carry an ``ImageRef`` rather than a pre-resolved id.
        """
        image_id: ImageID | None = None
        image_ref = spec.image.optional_value()
        if image_ref is not None:
            arch = (
                image_ref.architecture.value()
                if image_ref.architecture.optional_value()
                else "x86_64"
            )
            image_id = await self._deployment_repository.get_image_id(
                ImageIdentifier(image_ref.name, arch)
            )

        resource_slots_override = spec.resource_slots.optional_value()
        resource_slots_mapping: dict[str, str] | None
        if resource_slots_override is not None:
            resource_slots_mapping = {k: str(v) for k, v in resource_slots_override.items()}
        else:
            resource_slots_mapping = None

        resource_opts_override = spec.resource_opts.optional_value()
        environ_override = spec.environ.optional_value()

        return RevisionDraft(
            image_id=image_id,
            resource_slots=resource_slots_mapping,
            resource_opts=dict(resource_opts_override) if resource_opts_override else None,
            cluster_mode=spec.cluster_mode.optional_value(),
            cluster_size=spec.cluster_size.optional_value(),
            environ=dict(environ_override) if environ_override else None,
            runtime_variant_id=spec.runtime_variant_id.optional_value(),
        )

    async def validate_model_service(
        self, action: ValidateModelServiceAction
    ) -> ValidateModelServiceActionResult:
        if action.replicas > action.max_session_count_per_model_session:
            raise InvalidAPIParameters(
                f"Cannot spawn more than {action.max_session_count_per_model_session}"
                " sessions for a single service"
            )

        owner_access_key = action.owner_access_key
        if action.owner_access_key_override is not None:
            owner_access_key = action.owner_access_key_override

        extra_mounts_typed: dict[uuid.UUID, MountOptionModel] = {
            k: MountOptionModel(
                mount_destination=v.mount_destination,
                type=v.type,
                permission=v.permission,
                subpath=v.subpath,
            )
            for k, v in action.config.extra_mounts.items()
        }

        # Delegate all DB-dependent resolution to the repository.
        ctx = await self._repository.resolve_model_service_validation_context(
            scaling_group=action.config.scaling_group,
            owner_access_key=owner_access_key,
            domain_name=action.domain_name,
            group_name=action.group_name,
            requester_uuid=action.requester_uuid,
            requester_access_key=action.requester_access_key,
            requester_role=action.requester_role,
            requester_domain=action.requester_domain,
            keypair_resource_policy=action.keypair_resource_policy,
            owner_access_key_override=action.owner_access_key_override,
            model=action.config.model,
            model_mount_destination=action.config.model_mount_destination,
            extra_mounts=extra_mounts_typed,
            runtime_variant_name=str(action.runtime_variant),
            legacy_etcd_loader=self._config_provider.legacy_etcd_config_loader,
            storage_manager=self._storage_manager,
        )

        # Variants that read vfolder config files defer yaml parsing +
        # validation to ``RevisionDraftReader`` / ``ModelDefinition.to_resolved``
        # at draft construction time (single source of truth). Here we only
        # enforce the variant-specific mount-destination policy and pick the
        # yaml filename to thread through to the draft.
        if not ctx.variant_reads_vfolder_config_files:
            if (
                action.runtime_variant != "cmd"
                and action.config.model_mount_destination != "/models"
            ):
                raise InvalidAPIParameters(
                    "Model mount destination must be /models for non-custom runtimes"
                )
        yaml_path = action.config.model_definition_path or "model-definition.yaml"

        return ValidateModelServiceActionResult(
            model_vfolder_id=ctx.model_vfolder_id,
            model_definition_path=yaml_path,
            requester_access_key=ctx.requester_access_key,
            owner_access_key=ctx.owner_access_key,
            owner_uuid=ctx.owner_uuid,
            owner_role=ctx.owner_role,
            group_id=ctx.group_id,
            resource_policy=ctx.resource_policy,
            scaling_group=ctx.scaling_group,
            extra_mounts=ctx.extra_mounts,
        )
