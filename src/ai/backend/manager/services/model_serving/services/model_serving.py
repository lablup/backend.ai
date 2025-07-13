import asyncio
import logging
import secrets
import uuid
from http import HTTPStatus
from typing import Awaitable, Callable

import aiohttp
import tomli
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm.exc import NoResultFound
from yarl import URL

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.events.dispatcher import (
    EventDispatcher,
    EventHandler,
)
from ai.backend.common.events.event_types.kernel.types import (
    KernelLifecycleEventReason,
)
from ai.backend.common.events.event_types.model_serving.broadcast import (
    ModelServiceStatusBroadcastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SessionCancelledBroadcastEvent,
    SessionEnqueuedBroadcastEvent,
    SessionPreparingBroadcastEvent,
    SessionStartedBroadcastEvent,
    SessionTerminatedBroadcastEvent,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    ImageAlias,
    MountPermission,
    MountTypes,
    RuntimeVariant,
    SessionTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.constant import DEFAULT_CHUNK_SIZE
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.exceptions import (
    EndpointNotFound,
    ModelServiceNotFound,
    RouteNotFound,
)
from ai.backend.manager.models.endpoint import (
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
    ModelServicePredicateChecker,
)
from ai.backend.manager.models.group import resolve_group_name_or_id
from ai.backend.manager.models.image import ImageIdentifier, ImageRow
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry
from ai.backend.manager.models.vfolder import VFolderOwnershipType, VFolderRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.services.model_serving.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_serving.actions.create_model_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
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
from ai.backend.manager.services.model_serving.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import (
    InvalidAPIParameters,
)
from ai.backend.manager.services.model_serving.types import (
    CompactServiceInfo,
    EndpointData,
    ErrorInfo,
    ModelServiceDefinition,
    MutationResult,
    RouteInfo,
    ServiceInfo,
)
from ai.backend.manager.types import MountOptionModel, UserScope

log = BraceStyleAdapter(logging.getLogger(__name__))


class ModelServingService:
    _agent_registry: AgentRegistry
    _background_task_manager: BackgroundTaskManager
    _event_dispatcher: EventDispatcher
    _storage_manager: StorageSessionManager
    _config_provider: ManagerConfigProvider
    _repositories: ModelServingRepositories

    def __init__(
        self,
        agent_registry: AgentRegistry,
        background_task_manager: BackgroundTaskManager,
        event_dispatcher: EventDispatcher,
        storage_manager: StorageSessionManager,
        config_provider: ManagerConfigProvider,
        repositories: ModelServingRepositories,
    ) -> None:
        self._agent_registry = agent_registry
        self._background_task_manager = background_task_manager
        self._event_dispatcher = event_dispatcher
        self._storage_manager = storage_manager
        self._config_provider = config_provider
        self._repositories = repositories

    @property
    def _db(self) -> ExtendedAsyncSAEngine:
        """Access to database through repository for external service integrations."""
        return self._repositories.repository._db

    async def _fetch_file_from_storage_proxy(
        self,
        filename: str,
        model_vfolder_row: VFolderRow,
    ) -> bytes:
        vfid = model_vfolder_row.vfid
        folder_host = model_vfolder_row.host

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(folder_host)

        chunks = bytes()
        async with self._storage_manager.request(
            proxy_name,
            "POST",
            "folder/file/fetch",
            json={
                "volume": volume_name,
                "vfid": str(vfid),
                "relpath": f"./{filename}",
            },
        ) as (_, storage_resp):
            while True:
                chunk = await storage_resp.content.read(DEFAULT_CHUNK_SIZE)
                if not chunk:
                    break
                chunks += chunk
        return chunks

    async def create(self, action: CreateModelServiceAction) -> CreateModelServiceActionResult:
        service_prepare_ctx = action.creator.model_service_prepare_ctx

        # Get model vfolder
        model_vfolder_row = await self._repositories.repository.get_vfolder_by_id(
            service_prepare_ctx.model_id
        )
        if not model_vfolder_row:
            raise InvalidAPIParameters("Model vfolder not found")
        if model_vfolder_row.ownership_type == VFolderOwnershipType.GROUP:
            raise InvalidAPIParameters(
                "Cannot create model service with the project type's vfolder"
            )

        chunks = await self._fetch_file_from_storage_proxy(
            "service-definition.toml", model_vfolder_row
        )

        if chunks:
            raw_service_definition = chunks.decode("utf-8")
            service_definition = tomli.loads(raw_service_definition)

            definition = action.creator.runtime_variant
            if definition in service_definition:
                variant_def = ModelServiceDefinition.model_validate(service_definition[definition])
                if variant_def.resource_slots:
                    action.creator.config.resources = variant_def.resource_slots
                if variant_def.environment:
                    action.creator.image = variant_def.environment.image
                    action.creator.architecture = variant_def.environment.architecture
                if variant_def.environ:
                    if action.creator.config.environ:
                        action.creator.config.environ.update(variant_def.environ)
                    else:
                        action.creator.config.environ = variant_def.environ

        # Resolve image row using repository pattern
        async with self._db.begin_readonly_session() as db_sess:
            image_row = await ImageRow.resolve(
                db_sess,
                [
                    ImageIdentifier(action.creator.image, action.creator.architecture),
                    ImageAlias(action.creator.image),
                ],
            )

        creation_config = action.creator.config.to_dict()
        creation_config["mounts"] = [
            service_prepare_ctx.model_id,
            *[m.vfid.folder_id for m in service_prepare_ctx.extra_mounts],
        ]
        creation_config["mount_map"] = {
            service_prepare_ctx.model_id: action.creator.config.model_mount_destination,
            **{
                m.vfid.folder_id: m.kernel_path.as_posix() for m in service_prepare_ctx.extra_mounts
            },
        }
        creation_config["mount_options"] = {
            m.vfid.folder_id: {"permission": m.mount_perm} for m in service_prepare_ctx.extra_mounts
        }
        sudo_session_enabled = action.creator.sudo_session_enabled

        # check if session is valid to be created
        await self._agent_registry.create_session(
            "",
            image_row.image_ref,
            UserScope(
                domain_name=action.creator.domain_name,
                group_id=service_prepare_ctx.group_id,
                user_uuid=service_prepare_ctx.owner_uuid,
                user_role=service_prepare_ctx.owner_role,
            ),
            service_prepare_ctx.owner_access_key,
            service_prepare_ctx.resource_policy,
            SessionTypes.INFERENCE,
            creation_config,
            action.creator.cluster_mode,
            action.creator.cluster_size,
            dry_run=True,  # Setting this to True will prevent actual session from being enqueued
            bootstrap_script=action.creator.bootstrap_script,
            startup_command=action.creator.startup_command,
            tag=action.creator.tag,
            callback_url=URL(action.creator.callback_url.unicode_string())
            if action.creator.callback_url
            else None,
            sudo_session_enabled=sudo_session_enabled,
        )

        # Check endpoint name uniqueness
        is_name_available = await self._repositories.repository.check_endpoint_name_uniqueness(
            action.creator.service_name
        )
        if not is_name_available:
            raise InvalidAPIParameters("Cannot create multiple services with same name")

        async with self._db.begin_readonly_session() as db_sess:
            project_id = await resolve_group_name_or_id(
                await db_sess.connection(), action.creator.domain_name, action.creator.group_name
            )
            if project_id is None:
                raise InvalidAPIParameters(f"Invalid group name {project_id}")

        endpoint = EndpointRow(
            action.creator.service_name,
            service_prepare_ctx.model_definition_path,
            action.request_user_id,
            service_prepare_ctx.owner_uuid,
            action.creator.replicas,
            image_row,
            service_prepare_ctx.model_id,
            action.creator.domain_name,
            project_id,
            service_prepare_ctx.scaling_group,
            action.creator.config.resources,
            action.creator.cluster_mode,
            action.creator.cluster_size,
            service_prepare_ctx.extra_mounts,
            model_mount_destination=action.creator.config.model_mount_destination,
            tag=action.creator.tag,
            startup_command=action.creator.startup_command,
            callback_url=URL(action.creator.callback_url.unicode_string())
            if action.creator.callback_url
            else None,
            environ=action.creator.config.environ,
            bootstrap_script=action.creator.bootstrap_script,
            resource_opts=action.creator.config.resource_opts,
            open_to_public=action.creator.open_to_public,
            runtime_variant=action.creator.runtime_variant,
        )

        endpoint_data = await self._repositories.repository.create_endpoint_validated(endpoint)
        endpoint_id = endpoint_data.id

        return CreateModelServiceActionResult(
            ServiceInfo(
                endpoint_id=endpoint_id,
                model_id=endpoint.model,
                extra_mounts=[m.vfid.folder_id for m in endpoint.extra_mounts],
                name=action.creator.service_name,
                model_definition_path=service_prepare_ctx.model_definition_path,
                replicas=endpoint.replicas,
                desired_session_count=endpoint.replicas,
                active_routes=[],
                service_endpoint=None,
                is_public=action.creator.open_to_public,
                runtime_variant=action.creator.runtime_variant,
            )
        )

    async def list_serve(self, action: ListModelServiceAction) -> ListModelServiceActionResult:
        endpoints = await self._repositories.repository.list_endpoints_by_owner_validated(
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
                        r for r in endpoint.routings if r.status == RouteStatus.HEALTHY
                    ])
                    if endpoint.routings
                    else 0,
                    service_endpoint=endpoint.url,
                    is_public=endpoint.open_to_public,
                )
                for endpoint in endpoints
            ]
        )

    async def delete(self, action: DeleteModelServiceAction) -> DeleteModelServiceActionResult:
        service_id = action.service_id

        # Get endpoint with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            endpoint_data = await self._repositories.admin_repository.get_endpoint_by_id_force(
                service_id
            )
        else:
            endpoint_data = await self._repositories.repository.get_endpoint_by_id_validated(
                service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

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
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            await self._repositories.admin_repository.update_endpoint_lifecycle_force(
                service_id, lifecycle_stage, replicas
            )
        else:
            await self._repositories.repository.update_endpoint_lifecycle_validated(
                service_id,
                lifecycle_stage,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
                replicas,
            )

        return DeleteModelServiceActionResult(success=True)

    async def dry_run(self, action: DryRunModelServiceAction) -> DryRunModelServiceActionResult:
        # TODO: Seperate background task definition and trigger into different layer
        service_prepare_ctx = action.model_service_prepare_ctx
        # Get user with keypair
        created_user = await self._repositories.repository.get_user_with_keypair(
            action.request_user_id
        )
        if not created_user:
            raise InvalidAPIParameters("User not found")

        async with self._db.begin_readonly_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(action.image, action.architecture),
                    ImageAlias(action.image),
                ],
            )

        creation_config = action.config.to_dict()
        creation_config["mount_map"] = {
            service_prepare_ctx.model_id: action.config.model_mount_destination
        }
        sudo_session_enabled = action.sudo_session_enabled

        async def _task(reporter: ProgressReporter) -> None:
            terminated_event = asyncio.Event()

            result = await self._agent_registry.create_session(
                f"model-eval-{secrets.token_urlsafe(16)}",
                image_row.image_ref,
                UserScope(
                    domain_name=action.domain_name,
                    group_id=service_prepare_ctx.group_id,
                    user_uuid=created_user.uuid,
                    user_role=created_user.role,
                ),
                service_prepare_ctx.owner_access_key,
                service_prepare_ctx.resource_policy,
                SessionTypes.INFERENCE,
                {
                    "mounts": [
                        service_prepare_ctx.model_id,
                        *[m.vfid for m in service_prepare_ctx.extra_mounts],
                    ],
                    "mount_map": {
                        service_prepare_ctx.model_id: action.config.model_mount_destination,
                        **{m.vfid: m.kernel_path for m in service_prepare_ctx.extra_mounts},
                    },
                    "mount_options": {
                        m.vfid: {"permission": m.mount_perm}
                        for m in service_prepare_ctx.extra_mounts
                    },
                    "model_definition_path": service_prepare_ctx.model_definition_path,
                    "environ": creation_config["environ"],
                    "scaling_group": service_prepare_ctx.scaling_group,
                    "resources": creation_config["resources"],
                    "resource_opts": creation_config["resource_opts"],
                    "preopen_ports": None,
                    "agent_list": None,
                },
                action.cluster_mode,
                action.cluster_size,
                bootstrap_script=action.bootstrap_script,
                startup_command=action.startup_command,
                tag=action.tag,
                callback_url=URL(action.callback_url.unicode_string())
                if action.callback_url
                else None,
                enqueue_only=True,
                sudo_session_enabled=sudo_session_enabled,
            )

            await reporter.update(
                message=dump_json_str({
                    "event": "session_enqueued",
                    "session_id": str(result["sessionId"]),
                })
            )

            async def _handle_event(
                context: None,
                source: AgentId,
                event: SessionEnqueuedBroadcastEvent
                | SessionPreparingBroadcastEvent
                | SessionStartedBroadcastEvent
                | SessionCancelledBroadcastEvent
                | SessionTerminatedBroadcastEvent
                | ModelServiceStatusBroadcastEvent,
            ) -> None:
                task_message = {"event": event.event_name(), "session_id": str(event.session_id)}
                match event:
                    case ModelServiceStatusBroadcastEvent():
                        task_message["is_healthy"] = event.new_status.value
                await reporter.update(message=dump_json_str(task_message))

                match event:
                    case SessionTerminatedBroadcastEvent() | SessionCancelledBroadcastEvent():
                        terminated_event.set()
                    case ModelServiceStatusBroadcastEvent():
                        async with self._db.begin_readonly_session() as db_sess:
                            session = await SessionRow.get_session(
                                db_sess,
                                result["sessionId"],
                                None,
                                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                            )
                            await self._agent_registry.destroy_session(
                                session,
                                forced=True,
                            )

            session_event_matcher = lambda args: args[0] == str(result["sessionId"])
            model_service_event_matcher = lambda args: args[1] == str(result["sessionId"])

            handlers: list[EventHandler] = [
                self._event_dispatcher.subscribe(
                    SessionPreparingBroadcastEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    SessionStartedBroadcastEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    SessionCancelledBroadcastEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    SessionTerminatedBroadcastEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    ModelServiceStatusBroadcastEvent,
                    None,
                    _handle_event,
                    args_matcher=model_service_event_matcher,
                ),
            ]

            try:
                await terminated_event.wait()
            finally:
                for handler in handlers:
                    self._event_dispatcher.unsubscribe(handler)

        task_id = await self._background_task_manager.start(_task)
        return DryRunModelServiceActionResult(task_id)

    async def get_model_service_info(
        self, action: GetModelServiceInfoAction
    ) -> GetModelServiceInfoActionResult:
        # Get endpoint with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            endpoint_data = await self._repositories.admin_repository.get_endpoint_by_id_force(
                action.service_id
            )
        else:
            endpoint_data = await self._repositories.repository.get_endpoint_by_id_validated(
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not endpoint_data:
            raise ModelServiceNotFound

        return GetModelServiceInfoActionResult(
            ServiceInfo(
                endpoint_id=endpoint_data.id,
                model_id=endpoint_data.model,
                extra_mounts=[m.vfid.folder_id for m in endpoint_data.extra_mounts],
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
                service_endpoint=endpoint_data.url,
                is_public=endpoint_data.open_to_public,
                runtime_variant=endpoint_data.runtime_variant,
            )
        )

    async def list_errors(self, action: ListErrorsAction) -> ListErrorsActionResult:
        # Get endpoint with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            endpoint_data = await self._repositories.admin_repository.get_endpoint_by_id_force(
                action.service_id
            )
        else:
            endpoint_data = await self._repositories.repository.get_endpoint_by_id_validated(
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

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
        # Clear errors with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            success = await self._repositories.admin_repository.clear_endpoint_errors_force(
                action.service_id
            )
        else:
            success = await self._repositories.repository.clear_endpoint_errors_validated(
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not success:
            raise ModelServiceNotFound

        return ClearErrorActionResult(success=True)

    async def update_route(self, action: UpdateRouteAction) -> UpdateRouteActionResult:
        # Update route traffic with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            endpoint_data = await self._repositories.admin_repository.update_route_traffic_force(
                action.route_id, action.service_id, action.traffic_ratio
            )
        else:
            endpoint_data = await self._repositories.repository.update_route_traffic_validated(
                action.route_id,
                action.service_id,
                action.traffic_ratio,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not endpoint_data:
            raise RouteNotFound

        # Update AppProxy routes
        endpoint_row = await self._repositories.repository.get_endpoint_for_appproxy_update(
            action.service_id
        )
        if endpoint_row:
            async with self._db.begin_session() as db_sess:
                try:
                    await self._agent_registry.update_appproxy_endpoint_routes(
                        db_sess,
                        endpoint_row,
                        [r for r in endpoint_row.routings if r.status == RouteStatus.HEALTHY],
                    )
                except aiohttp.ClientError as e:
                    log.warning("failed to communicate with AppProxy endpoint: {}", str(e))

        return UpdateRouteActionResult(success=True)

    async def delete_route(self, action: DeleteRouteAction) -> DeleteRouteActionResult:
        # Get route with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            route_data = await self._repositories.admin_repository.get_route_by_id_force(
                action.route_id, action.service_id
            )
        else:
            route_data = await self._repositories.repository.get_route_by_id_validated(
                action.route_id,
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not route_data:
            raise RouteNotFound

        if route_data.status == RouteStatus.PROVISIONING:
            raise InvalidAPIParameters("Cannot remove route in PROVISIONING status")

        # Get session for destruction
        route_row = await self._repositories.repository.get_route_with_session(action.route_id)
        if not route_row:
            raise RouteNotFound

        await self._agent_registry.destroy_session(
            route_row.session_row,
            forced=False,
            reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN,
        )

        # Decrease endpoint replicas
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            await self._repositories.admin_repository.decrease_endpoint_replicas_force(
                action.service_id
            )
        else:
            await self._repositories.repository.decrease_endpoint_replicas_validated(
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        return DeleteRouteActionResult(success=True)

    async def generate_token(self, action: GenerateTokenAction) -> GenerateTokenActionResult:
        # Get endpoint with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            endpoint_data = await self._repositories.admin_repository.get_endpoint_by_id_force(
                action.service_id
            )
        else:
            endpoint_data = await self._repositories.repository.get_endpoint_by_id_validated(
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not endpoint_data:
            raise ModelServiceNotFound

        # Get scaling group info
        scaling_group_data = await self._repositories.repository.get_scaling_group_info(
            endpoint_data.resource_group
        )
        if not scaling_group_data:
            raise InvalidAPIParameters(f"Scaling group {endpoint_data.resource_group} not found")

        # Generate token via wsproxy
        body = {"user_uuid": str(endpoint_data.session_owner_id), "exp": action.expires_at}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{scaling_group_data.wsproxy_addr}/v2/endpoints/{endpoint_data.id}/token",
                json=body,
                headers={
                    "accept": "application/json",
                    "X-BackendAI-Token": scaling_group_data.wsproxy_api_token,
                },
            ) as resp:
                resp_json = await resp.json()
                if resp.status != HTTPStatus.OK:
                    raise EndpointNotFound(
                        f"Failed to generate token: {resp.status} {resp.reason} {resp_json}"
                    )
                token = resp_json["token"]

        # Create token in database
        token_id = uuid.uuid4()
        token_row = EndpointTokenRow(
            token_id,
            token,
            endpoint_data.id,
            endpoint_data.domain,
            endpoint_data.project,
            endpoint_data.session_owner_id,
        )

        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            token_data = await self._repositories.admin_repository.create_endpoint_token_force(
                token_row
            )
        else:
            token_data = await self._repositories.repository.create_endpoint_token_validated(
                token_row,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not token_data:
            raise ModelServiceNotFound

        return GenerateTokenActionResult(token_data)

    async def force_sync_with_app_proxy(self, action: ForceSyncAction) -> ForceSyncActionResult:
        # Get endpoint with access validation
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            endpoint_data = await self._repositories.admin_repository.get_endpoint_by_id_force(
                action.service_id
            )
        else:
            endpoint_data = await self._repositories.repository.get_endpoint_by_id_validated(
                action.service_id,
                action.requester_ctx.user_id,
                action.requester_ctx.user_role,
                action.requester_ctx.domain_name,
            )

        if not endpoint_data:
            raise ModelServiceNotFound

        # Sync with AppProxy
        endpoint_row = await self._repositories.repository.get_endpoint_for_appproxy_update(
            action.service_id
        )
        if endpoint_row:
            async with self._db.begin_session() as db_sess:
                await self._agent_registry.update_appproxy_endpoint_routes(
                    db_sess,
                    endpoint_row,
                    [r for r in endpoint_row.routings if r.status == RouteStatus.HEALTHY],
                )

        return ForceSyncActionResult(success=True)

    async def modify_endpoint(self, action: ModifyEndpointAction) -> ModifyEndpointActionResult:
        async def _do_mutate() -> MutationResult:
            async with self._db.begin_session() as db_session:
                try:
                    endpoint_row = await EndpointRow.get(
                        db_session,
                        action.endpoint_id,
                        load_session_owner=True,
                        load_model=True,
                        load_routes=True,
                    )
                    match action.requester_ctx.user_role:
                        case UserRole.SUPERADMIN:
                            pass
                        case UserRole.ADMIN:
                            domain_name = action.requester_ctx.domain_name
                            if endpoint_row.domain != domain_name:
                                raise EndpointNotFound
                        case _:
                            user_id = action.requester_ctx.user_id
                            if endpoint_row.session_owner != user_id:
                                raise EndpointNotFound
                except NoResultFound:
                    raise EndpointNotFound
                if endpoint_row.lifecycle_stage in (
                    EndpointLifecycle.DESTROYING,
                    EndpointLifecycle.DESTROYED,
                ):
                    raise InvalidAPIParameters("Cannot update endpoint marked for removal")

                fields_to_update = action.modifier.fields_to_update()
                for key, value in fields_to_update.items():
                    setattr(endpoint_row, key, value)

                fields_to_update_require_none_check = (
                    action.modifier.fields_to_update_require_none_check()
                )
                for key, value in fields_to_update_require_none_check.items():
                    if value is not None:
                        setattr(endpoint_row, key, value)

                image_ref = action.modifier.image.optional_value()
                if image_ref is not None:
                    image_name = image_ref.name
                    arch = image_ref.architecture.value()
                    image_row = await ImageRow.resolve(
                        db_session, [ImageIdentifier(image_name, arch), ImageAlias(image_name)]
                    )
                    endpoint_row.image = image_row.id

                session_owner: UserRow = endpoint_row.session_owner_row

                conn = await db_session.connection()
                assert conn

                await ModelServicePredicateChecker.check_scaling_group(
                    conn,
                    endpoint_row.resource_group,
                    session_owner.main_access_key,
                    endpoint_row.domain,
                    endpoint_row.project,
                )

                user_scope = UserScope(
                    domain_name=endpoint_row.domain,
                    group_id=endpoint_row.project,
                    user_uuid=session_owner.uuid,
                    user_role=session_owner.role,
                )

                resource_policy = await self._repositories.repository.get_keypair_resource_policy(
                    session_owner.resource_policy
                )
                if not resource_policy:
                    raise InvalidAPIParameters("Resource policy not found")
                extra_mounts_input = action.modifier.extra_mounts.optional_value()
                if extra_mounts_input is not None:
                    extra_mounts = {
                        mount.vfolder_id.value(): MountOptionModel(
                            mount_destination=(
                                mount.mount_destination.value()
                                if mount.mount_destination.optional_value() is not None
                                else None
                            ),
                            type=MountTypes(mount.type.value())
                            if mount.type.optional_value() is not None
                            else MountTypes.BIND,
                            permission=(
                                MountPermission(mount.permission.value())
                                if mount.permission.optional_value() is not None
                                else None
                            ),
                        )
                        for mount in extra_mounts_input
                    }
                    vfolder_mounts = await ModelServicePredicateChecker.check_extra_mounts(
                        conn,
                        self._config_provider.legacy_etcd_config_loader,
                        self._storage_manager,
                        endpoint_row.model,
                        endpoint_row.model_mount_destination,
                        extra_mounts,
                        user_scope,
                        resource_policy,
                    )
                    endpoint_row.extra_mounts = vfolder_mounts

                if endpoint_row.runtime_variant == RuntimeVariant.CUSTOM:
                    await ModelServicePredicateChecker.validate_model_definition(
                        self._storage_manager,
                        endpoint_row.model_row,
                        endpoint_row.model_definition_path,
                    )
                elif (
                    endpoint_row.runtime_variant != RuntimeVariant.CMD
                    and endpoint_row.model_mount_destination != "/models"
                ):
                    raise InvalidAPIParameters(
                        "Model mount destination must be /models for non-custom runtimes"
                    )

                async with self._db.begin_session() as db_session:
                    image_row = await ImageRow.resolve(
                        db_session,
                        [
                            ImageIdentifier(
                                endpoint_row.image_row.name, endpoint_row.image_row.architecture
                            ),
                        ],
                    )

                await self._agent_registry.create_session(
                    "",
                    image_row.image_ref,
                    user_scope,
                    session_owner.main_access_key,
                    resource_policy,
                    SessionTypes.INFERENCE,
                    {
                        "mounts": [
                            endpoint_row.model,
                            *[m.vfid.folder_id for m in endpoint_row.extra_mounts],
                        ],
                        "mount_map": {
                            endpoint_row.model: endpoint_row.model_mount_destination,
                            **{
                                m.vfid.folder_id: m.kernel_path.as_posix()
                                for m in endpoint_row.extra_mounts
                            },
                        },
                        "mount_options": {
                            m.vfid.folder_id: {"permission": m.mount_perm}
                            for m in endpoint_row.extra_mounts
                        },
                        "environ": endpoint_row.environ,
                        "scaling_group": endpoint_row.resource_group,
                        "resources": endpoint_row.resource_slots,
                        "resource_opts": endpoint_row.resource_opts,
                        "preopen_ports": None,
                        "agent_list": None,
                    },
                    ClusterMode(endpoint_row.cluster_mode),
                    endpoint_row.cluster_size,
                    bootstrap_script=endpoint_row.bootstrap_script,
                    startup_command=endpoint_row.startup_command,
                    tag=endpoint_row.tag,
                    callback_url=endpoint_row.callback_url,
                    sudo_session_enabled=session_owner.sudo_session_enabled,
                    dry_run=True,
                )

                await db_session.commit()
                return MutationResult(
                    success=True,
                    message="success",
                    data=EndpointData.from_row(endpoint_row),
                )

        result = await self._db_mutation_wrapper(_do_mutate)
        return ModifyEndpointActionResult(success=result.success, data=result.data)

    async def _db_mutation_wrapper(
        self, _do_mutate: Callable[[], Awaitable[MutationResult]]
    ) -> MutationResult:
        try:
            return await execute_with_retry(_do_mutate)
        except IntegrityError as e:
            log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
            return MutationResult(success=False, message=f"integrity error: {e}", data=None)
        except StatementError as e:
            log.warning(
                "db_mutation_wrapper(): statement error ({})\n{}",
                repr(e),
                e.statement or "(unknown)",
            )
            orig_exc = e.orig
            return MutationResult(success=False, message=str(orig_exc), data=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception:
            log.exception("db_mutation_wrapper(): other error")
            raise
