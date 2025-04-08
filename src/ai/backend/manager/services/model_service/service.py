import asyncio
import decimal
import logging
import secrets
import uuid
from typing import Any, Awaitable, Callable, cast

import aiohttp
import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound
from yarl import URL

from ai.backend.common.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.events import (
    EventDispatcher,
    EventHandler,
    KernelLifecycleEventReason,
    ModelServiceStatusEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionPreparingEvent,
    SessionStartedEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    EndpointId,
    ImageAlias,
    MountPermission,
    MountTypes,
    ResourceSlot,
    RuleId,
    RuntimeVariant,
    SessionTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config import SharedConfig
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
    ModelServicePredicateChecker,
)
from ai.backend.manager.models.group import resolve_group_name_or_id
from ai.backend.manager.models.image import ImageIdentifier, ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.model_service.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_service.actions.create_endpoint_auto_scaling_rule import (
    CreateEndpointAutoScalingRuleAction,
    CreateEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.create_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
    ServiceInfo,
)
from ai.backend.manager.services.model_service.actions.delete_enpoint_auto_scaling_rule import (
    DeleteEndpointAutoScalingRuleAction,
    DeleteEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_route import (
    DeleteRouteAction,
    DeleteRouteActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_service.actions.get_info import (
    GetInfoAction,
    GetInfoActionResult,
)
from ai.backend.manager.services.model_service.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_service.actions.list_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.modify_endpoint_auto_scaling_rule import (
    ModifyEndpointAutoScalingRuleAction,
    ModifyEndpointAutoScalingRuleActionResult,
)
from ai.backend.manager.services.model_service.actions.modify_enpoint import (
    ExtraMount,
    ImageRef,
    ModifyEndpointAction,
    ModifyEndpointActionResult,
)
from ai.backend.manager.services.model_service.actions.scale import ScaleAction, ScaleActionResult
from ai.backend.manager.services.model_service.actions.start_service import (
    StartModelServiceAction,
    StartModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.sync import SyncAction, SyncActionResult
from ai.backend.manager.services.model_service.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_service.exceptions import (
    EndpointAutoScalingRuleNotFound,
    EndpointNotFound,
    GenericForbidden,
    InvalidAPIParameters,
    ModelServiceNotFound,
)
from ai.backend.manager.services.model_service.types import (
    CompactServiceInfo,
    EndpointAutoScalingRuleData,
    EndpointData,
    ErrorInfo,
    MutationResult,
    RequesterCtx,
    RouteInfo,
)
from ai.backend.manager.types import MountOptionModel, State, UserScope
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user_uuid

log = BraceStyleAdapter(logging.getLogger(__name__))


class ModelService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry
    _background_task_manager: BackgroundTaskManager
    _event_dispatcher: EventDispatcher
    _storage_manager: StorageSessionManager
    _shared_config: SharedConfig

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        background_task_manager: BackgroundTaskManager,
        event_dispatcher: EventDispatcher,
        storage_manager: StorageSessionManager,
        shared_config: SharedConfig,
    ) -> None:
        self._db = db
        self._registry = agent_registry
        self._background_task_manager = background_task_manager
        self._event_dispatcher = event_dispatcher
        self._storage_manager = storage_manager
        self._shared_config = shared_config

    async def create(self, action: CreateModelServiceAction) -> CreateModelServiceActionResult:
        validation_result = action.validation_result
        async with self._db.begin_readonly_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(action.image, action.architecture),
                    ImageAlias(action.image),
                ],
            )

        creation_config = action.config.to_dict()
        creation_config["mounts"] = [
            validation_result.model_id,
            *[m.vfid.folder_id for m in validation_result.extra_mounts],
        ]
        creation_config["mount_map"] = {
            validation_result.model_id: action.config.model_mount_destination,
            **{m.vfid.folder_id: m.kernel_path.as_posix() for m in validation_result.extra_mounts},
        }
        creation_config["mount_options"] = {
            m.vfid.folder_id: {"permission": m.mount_perm} for m in validation_result.extra_mounts
        }
        sudo_session_enabled = action.sudo_session_enabled

        # check if session is valid to be created
        await self._agent_registry.create_session(
            "",
            image_row.image_ref,
            UserScope(
                domain_name=action.domain,
                group_id=validation_result.group_id,
                user_uuid=validation_result.owner_uuid,
                user_role=validation_result.owner_role,
            ),
            validation_result.owner_access_key,
            validation_result.resource_policy,
            SessionTypes.INFERENCE,
            creation_config,
            action.cluster_mode,
            action.cluster_size,
            dry_run=True,  # Setting this to True will prevent actual session from being enqueued
            bootstrap_script=action.bootstrap_script,
            startup_command=action.startup_command,
            tag=action.tag,
            callback_url=URL(action.callback_url.unicode_string()) if action.callback_url else None,
            sudo_session_enabled=sudo_session_enabled,
        )

        async with self._db.begin_session() as db_sess:
            query = sa.select(EndpointRow).where(
                (EndpointRow.lifecycle_stage != EndpointLifecycle.DESTROYED)
                & (EndpointRow.name == action.service_name)
            )
            result = await db_sess.execute(query)
            service_with_duplicate_name = result.scalar()
            if service_with_duplicate_name is not None:
                raise InvalidAPIParameters("Cannot create multiple services with same name")

            project_id = await resolve_group_name_or_id(
                await db_sess.connection(), action.domain, action.group
            )
            if project_id is None:
                raise InvalidAPIParameters(f"Invalid group name {project_id}")
            endpoint = EndpointRow(
                action.service_name,
                validation_result.model_definition_path,
                action.created_user_id,
                validation_result.owner_uuid,
                action.replicas,
                image_row,
                validation_result.model_id,
                action.domain,
                project_id,
                validation_result.scaling_group,
                action.config.resources,
                action.cluster_mode,
                action.cluster_size,
                validation_result.extra_mounts,
                model_mount_destination=action.config.model_mount_destination,
                tag=action.tag,
                startup_command=action.startup_command,
                callback_url=URL(action.callback_url.unicode_string())
                if action.callback_url
                else None,
                environ=action.config.environ,
                bootstrap_script=action.bootstrap_script,
                resource_opts=action.config.resource_opts,
                open_to_public=action.open_to_public,
                runtime_variant=action.runtime_variant,
            )
            db_sess.add(endpoint)
            await db_sess.flush()
            endpoint_id = endpoint.id

        return CreateModelServiceActionResult(
            ServiceInfo(
                endpoint_id=endpoint_id,
                model_id=endpoint.model,
                extra_mounts=[m.vfid.folder_id for m in endpoint.extra_mounts],
                name=action.service_name,
                model_definition_path=validation_result.model_definition_path,
                replicas=endpoint.replicas,
                desired_session_count=endpoint.replicas,
                active_routes=[],
                service_endpoint=None,
                is_public=action.open_to_public,
                runtime_variant=action.runtime_variant,
            )
        )

    async def list_serve(self, action: ListModelServiceAction) -> ListModelServiceActionResult:
        query_conds = (EndpointRow.session_owner == action.session_owener_id) & (
            EndpointRow.lifecycle_stage == EndpointLifecycle.CREATED
        )
        if action.name:
            query_conds &= EndpointRow.name == action.name

        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(EndpointRow)
                .where(query_conds)
                .options(selectinload(EndpointRow.routings))
            )
            result = await db_sess.execute(query)
            rows = result.scalars().all()

        return ListModelServiceActionResult(
            data=[
                CompactServiceInfo(
                    id=endpoint.id,
                    name=endpoint.name,
                    replicas=endpoint.replicas,
                    desired_session_count=endpoint.replicas,
                    active_route_count=len([
                        r for r in endpoint.routings if r.status == RouteStatus.HEALTHY
                    ]),
                    service_endpoint=endpoint.url,
                    is_public=endpoint.open_to_public,
                )
                for endpoint in rows
            ]
        )

    async def delete(self, action: DeleteModelServiceAction) -> DeleteModelServiceActionResult:
        service_id = action.service_id
        async with self._db.begin_readonly_session() as db_sess:
            try:
                endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
            except NoResultFound:
                raise ModelServiceNotFound
        await self._verify_user_access_scopes(action.requester_ctx, endpoint.session_owner)

        async with self._db.begin_session() as db_sess:
            if len(endpoint.routings) == 0:
                query = (
                    sa.update(EndpointRow)
                    .where(EndpointRow.id == service_id)
                    .values({"lifecycle_stage": EndpointLifecycle.DESTROYED})
                )
            else:
                query = (
                    sa.update(EndpointRow)
                    .where(EndpointRow.id == service_id)
                    .values({
                        "replicas": 0,
                        "lifecycle_stage": EndpointLifecycle.DESTROYING,
                    })
                )
            await db_sess.execute(query)

        return DeleteModelServiceActionResult(success=True)

    async def try_start(self, action: StartModelServiceAction) -> StartModelServiceActionResult:
        validation_result = action.validation_result
        async with self._db.begin_readonly_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(action.image, action.architecture),
                    ImageAlias(action.image),
                ],
            )
            query = sa.select(sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)).where(
                UserRow.uuid == action.owner_id
            )
            created_user = (await session.execute(query)).fetchone()

        creation_config = action.config.to_dict()
        creation_config["mount_map"] = {
            validation_result.model_id: action.config.model_mount_destination
        }
        sudo_session_enabled = action.sudo_session_enabled

        async def _task(reporter: ProgressReporter) -> None:
            terminated_event = asyncio.Event()

            result = await self._registry.create_session(
                f"model-eval-{secrets.token_urlsafe(16)}",
                image_row.image_ref,
                UserScope(
                    domain_name=action.domain,
                    group_id=validation_result.group_id,
                    user_uuid=created_user.uuid,
                    user_role=created_user.role,
                ),
                validation_result.owner_access_key,
                validation_result.resource_policy,
                SessionTypes.INFERENCE,
                {
                    "mounts": [
                        validation_result.model_id,
                        *[m.vfid for m in validation_result.extra_mounts],
                    ],
                    "mount_map": {
                        validation_result.model_id: action.config.model_mount_destination,
                        **{m.vfid: m.kernel_path for m in validation_result.extra_mounts},
                    },
                    "mount_options": {
                        m.vfid: {"permission": m.mount_perm} for m in validation_result.extra_mounts
                    },
                    "model_definition_path": validation_result.model_definition_path,
                    "environ": creation_config["environ"],
                    "scaling_group": validation_result.scaling_group,
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
                event: SessionEnqueuedEvent
                | SessionPreparingEvent
                | SessionStartedEvent
                | SessionCancelledEvent
                | SessionTerminatedEvent
                | ModelServiceStatusEvent,
            ) -> None:
                task_message = {"event": event.name, "session_id": str(event.session_id)}
                match event:
                    case ModelServiceStatusEvent():
                        task_message["is_healthy"] = event.new_status.value
                await reporter.update(message=dump_json_str(task_message))

                match event:
                    case SessionTerminatedEvent() | SessionCancelledEvent():
                        terminated_event.set()
                    case ModelServiceStatusEvent():
                        async with self._db.begin_readonly_session() as db_sess:
                            session = await SessionRow.get_session(
                                db_sess,
                                result["sessionId"],
                                None,
                                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                            )
                            await self._registry.destroy_session(
                                session,
                                forced=True,
                            )

            session_event_matcher = lambda args: args[0] == str(result["sessionId"])
            model_service_event_matcher = lambda args: args[1] == str(result["sessionId"])

            handlers: list[EventHandler] = [
                self._event_dispatcher.subscribe(
                    SessionPreparingEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    SessionStartedEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    SessionCancelledEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    SessionTerminatedEvent,
                    None,
                    _handle_event,
                    args_matcher=session_event_matcher,
                ),
                self._event_dispatcher.subscribe(
                    ModelServiceStatusEvent,
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
        return StartModelServiceActionResult(task_id)

    async def get_info(self, action: GetInfoAction) -> GetInfoActionResult:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                endpoint = await EndpointRow.get(db_sess, action.service_id, load_routes=True)
            except NoResultFound:
                raise ModelServiceNotFound

        return GetInfoActionResult(
            ServiceInfo(
                endpoint_id=endpoint.id,
                model_id=endpoint.model,
                extra_mounts=[m.vfid.folder_id for m in endpoint.extra_mounts],
                name=endpoint.name,
                model_definition_path=endpoint.model_definition_path,
                replicas=endpoint.replicas,
                desired_session_count=endpoint.replicas,
                active_routes=[
                    RouteInfo(
                        route_id=r.id,
                        session_id=r.session_id,
                        traffic_ratio=r.traffic_ratio,
                    )
                    for r in endpoint.routings
                ],
                service_endpoint=endpoint.url,
                is_public=endpoint.open_to_public,
                runtime_variant=endpoint.runtime_variant,
            )
        )

    async def list_errors(self, action: ListErrorsAction) -> ListErrorsActionResult:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                endpoint = await EndpointRow.get(db_sess, action.service_id, load_routes=True)
            except NoResultFound:
                raise ModelServiceNotFound

        await self._verify_user_access_scopes(action.requester_ctx, endpoint.session_owner)

        error_routes = [r for r in endpoint.routings if r.status == RouteStatus.FAILED_TO_START]

        return ListErrorsActionResult(
            error_info=[
                ErrorInfo(
                    session_id=route.error_data.get("session_id"), error=route.error_data["errors"]
                )
                for route in error_routes
            ],
            retries=endpoint.retries,
        )

    async def clear_error(self, action: ClearErrorAction) -> ClearErrorActionResult:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                endpoint = await EndpointRow.get(db_sess, action.service_id, load_routes=True)
            except NoResultFound:
                raise ModelServiceNotFound
        await self._verify_user_access_scopes(action.requester_ctx, endpoint.session_owner)

        async with self._db.begin_session() as db_sess:
            query = sa.delete(RoutingRow).where(
                (RoutingRow.endpoint == action.service_id)
                & (RoutingRow.status == RouteStatus.FAILED_TO_START)
            )
            await db_sess.execute(query)
            query = (
                sa.update(EndpointRow).values({"retries": 0}).where(EndpointRow.id == endpoint.id)
            )
            await db_sess.execute(query)

        return ClearErrorActionResult(success=True)

    async def scale(self, action: ScaleAction) -> ScaleActionResult:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                endpoint = await EndpointRow.get(db_sess, action.service_id, load_routes=True)
            except NoResultFound:
                raise ModelServiceNotFound
        await self._verify_user_access_scopes(action.requester_ctx, endpoint.session_owner)

        if action.to < 0:
            raise InvalidAPIParameters(
                "Amount of desired session count cannot be a negative number"
            )
        elif action.to > action.max_session_count_per_model_session:
            raise InvalidAPIParameters(
                f"Cannot spawn more than {action.max_session_count_per_model_session} sessions for a single service"
            )

        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == action.service_id)
                .values({"replicas": action.to})
            )
            await db_sess.execute(query)
            return ScaleActionResult(
                current_route_count=len(endpoint.routings), target_count=action.to
            )

    async def sync(self, action: SyncAction) -> SyncActionResult:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                endpoint = await EndpointRow.get(db_sess, action.service_id, load_routes=True)
            except NoResultFound:
                raise ModelServiceNotFound
        await self._verify_user_access_scopes(action.requester_ctx, endpoint.session_owner)

        async with self._db.begin_session() as db_sess:
            await self._registry.update_appproxy_endpoint_routes(
                db_sess, endpoint, [r for r in endpoint.routings if r.status == RouteStatus.HEALTHY]
            )

        return SyncActionResult(success=True)

    async def update_route(self, action: UpdateRouteAction) -> UpdateRouteActionResult:
        async with self._db.begin_session() as db_sess:
            try:
                route = await RoutingRow.get(db_sess, action.route_id, load_endpoint=True)
            except NoResultFound:
                raise ModelServiceNotFound
            if route.endpoint != action.service_id:
                raise ModelServiceNotFound
            await self._verify_user_access_scopes(
                action.requester_ctx, route.endpoint_row.session_owner
            )

            query = (
                sa.update(RoutingRow)
                .where(RoutingRow.id == action.route_id)
                .values({"traffic_ratio": action.traffic_ratio})
            )
            await db_sess.execute(query)
            endpoint = await EndpointRow.get(db_sess, action.service_id, load_routes=True)
            try:
                await self._registry.update_appproxy_endpoint_routes(
                    db_sess,
                    endpoint,
                    [r for r in endpoint.routes if r.status == RouteStatus.HEALTHY],
                )
            except aiohttp.ClientError as e:
                log.warning("failed to communicate with AppProxy endpoint: {}", str(e))

        return UpdateRouteActionResult(success=True)

    async def delete_route(self, action: DeleteRouteAction) -> DeleteRouteActionResult:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                route = await RoutingRow.get(db_sess, action.route_id, load_session=True)
            except NoResultFound:
                raise ModelServiceNotFound
            if route.endpoint != action.service_id:
                raise ModelServiceNotFound
        await self._verify_user_access_scopes(
            action.requester_ctx, route.endpoint_row.session_owner
        )
        if route.status == RouteStatus.PROVISIONING:
            raise InvalidAPIParameters("Cannot remove route in PROVISIONING status")

        await self._registry.destroy_session(
            route.session_row,
            forced=False,
            reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN,
        )

        async with self._db.begin_session() as db_sess:
            query = (
                sa.update(EndpointRow)
                .where(EndpointRow.id == action.service_id)
                .values({"replicas": route.endpoint_row.replicas - 1})
            )
            await db_sess.execute(query)

        return DeleteRouteActionResult(success=True)

    async def generate_token(self, action: GenerateTokenAction) -> GenerateTokenActionResult:
        async with self._db.begin_readonly_session() as db_sess:
            try:
                endpoint = await EndpointRow.get(db_sess, action.service_id, load_routes=True)
            except NoResultFound:
                raise ModelServiceNotFound
            query = (
                sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
                .select_from(scaling_groups)
                .where((scaling_groups.c.name == endpoint.resource_group))
            )

            result = await db_sess.execute(query)
            sgroup = result.first()
            wsproxy_addr = sgroup["wsproxy_addr"]
            wsproxy_api_token = sgroup["wsproxy_api_token"]

        await self._verify_user_access_scopes(action.requester_ctx, endpoint.session_owner)

        body = {"user_uuid": str(endpoint.session_owner), "exp": action.expires_at}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{wsproxy_addr}/v2/endpoints/{endpoint.id}/token",
                json=body,
                headers={
                    "X-BackendAI-Token": wsproxy_api_token,
                },
            ) as resp:
                token_json = await resp.json()
                token = token_json["token"]

        async with self._db.begin_session() as db_sess:
            token_row = EndpointTokenRow(
                uuid.uuid4(),
                token,
                endpoint.id,
                endpoint.domain,
                endpoint.project,
                endpoint.session_owner,
            )
            db_sess.add(token_row)
            await db_sess.commit()

        return GenerateTokenActionResult(token)

    async def _verify_user_access_scopes(
        self, requester_ctx: RequesterCtx, owner_uuid: uuid.UUID
    ) -> None:
        if not requester_ctx.is_authorized:
            raise GenericForbidden("Only authorized requests may have access key scopes.")
        if owner_uuid is None or owner_uuid == requester_ctx.user_id:
            return
        async with self._db.begin_readonly() as conn:
            try:
                await check_if_requester_is_eligible_to_act_as_target_user_uuid(
                    conn,
                    requester_ctx.user_role,
                    requester_ctx.domain_name,
                    owner_uuid,
                )
                return
            except ValueError as e:
                raise InvalidAPIParameters(str(e))
            except RuntimeError as e:
                raise GenericForbidden(str(e))

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

                if action.resource_slots.state() == State.UPDATE:
                    endpoint_row.resource_slots = ResourceSlot.from_user_input(
                        cast(dict[str, Any], action.resource_slots.value()), None
                    )

                action.resource_opts.set_attr(endpoint_row)
                action.cluster_mode.set_attr(endpoint_row)
                action.cluster_size.set_attr(endpoint_row)
                action.model_definition_path.set_attr(endpoint_row)

                if action.environ.state() == State.UPDATE and action.environ.value() is not None:
                    endpoint_row.environ = action.environ.value()

                if action.runtime_variant.state() == State.UPDATE:
                    try:
                        endpoint_row.runtime_variant = RuntimeVariant(
                            cast(str, action.runtime_variant.value())
                        )
                    except KeyError:
                        raise InvalidAPIParameters(
                            f"Unsupported runtime {action.runtime_variant.value()}"
                        )

                if (
                    action.desired_session_count.state() == State.UPDATE
                    and action.replicas.state() == State.UPDATE
                ):
                    raise InvalidAPIParameters(
                        "Cannot set both desired_session_count and replicas. Use replicas for future use."
                    )

                if (
                    action.desired_session_count.state() == State.UPDATE
                    and action.desired_session_count.value() is not None
                ):
                    endpoint_row.replicas = action.desired_session_count.value()

                if action.replicas.state() == State.UPDATE and action.replicas.value() is not None:
                    endpoint_row.replicas = action.replicas.value()

                action.resource_group.set_attr(endpoint_row)

                if action.image.state() == State.UPDATE and action:
                    image_ref = cast(ImageRef, action.image.value())
                    image_name = image_ref.name
                    arch = cast(str, image_ref.architecture.value())
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

                query = (
                    sa.select([keypair_resource_policies])
                    .select_from(keypair_resource_policies)
                    .where(keypair_resource_policies.c.name == session_owner.resource_policy)
                )
                result = await conn.execute(query)

                resource_policy = result.first()
                if action.extra_mounts.state() == State.UPDATE:
                    extra_mounts_input = cast(list[ExtraMount], action.extra_mounts.value())
                    extra_mounts = {
                        cast(uuid.UUID, m.vfolder_id.value()): MountOptionModel(
                            mount_destination=(
                                m.mount_destination.value()
                                if m.mount_destination.state() == State.UPDATE
                                else None
                            ),
                            type=MountTypes(cast(str, m.type.value()))
                            if m.type.state() == State.UPDATE
                            else MountTypes.BIND,
                            permission=(
                                MountPermission(cast(str, m.permission.value()))
                                if m.permission.state() == State.UPDATE
                                else None
                            ),
                        )
                        for m in extra_mounts_input
                    }
                    vfolder_mounts = await ModelServicePredicateChecker.check_extra_mounts(
                        conn,
                        self._shared_config,
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

                await self._registry.create_session(
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
                    ClusterMode[endpoint_row.cluster_mode],
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
                    data=endpoint_row,
                )

        result = await self._db_mutation_wrapper(_do_mutate)
        return ModifyEndpointActionResult(
            success=result.success, data=EndpointData.from_row(result.data)
        )

    async def create_endpoint_auto_scaling_rule(
        self, action: CreateEndpointAutoScalingRuleAction
    ) -> CreateEndpointAutoScalingRuleActionResult:
        if not action.metric_source:
            raise InvalidAPIParameters("metric_source is a required field")
        if not action.comparator:
            raise InvalidAPIParameters("comparator is a required field")

        try:
            _endpoint_id = EndpointId(action.endpoint_id)
        except ValueError:
            raise EndpointNotFound

        async with self._db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointRow.get(db_session, _endpoint_id)
            except NoResultFound:
                raise EndpointNotFound

            match action.requester_ctx.user_role:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.domain != action.requester_ctx.domain_name:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.created_user != action.requester_ctx.user_id:
                        raise GenericForbidden

            try:
                _threshold = decimal.Decimal(action.threshold)
            except decimal.InvalidOperation:
                raise InvalidAPIParameters(f"Cannot convert {action.threshold} to Decimal")

            async def _do_mutate() -> MutationResult:
                created_rule = await row.create_auto_scaling_rule(
                    db_session,
                    action.metric_source,
                    action.metric_name,
                    _threshold,
                    action.comparator,
                    action.step_size,
                    cooldown_seconds=action.cooldown_seconds,
                    min_replicas=action.min_replicas,
                    max_replicas=action.max_replicas,
                )
                return MutationResult(
                    success=True,
                    message="Auto scaling rule created",
                    data=created_rule,
                )

            res = await self._db_mutation_wrapper(_do_mutate)

            return CreateEndpointAutoScalingRuleActionResult(
                success=res.success,
                data=EndpointAutoScalingRuleData.from_row(res.data),
            )

    async def modify_endpoint_auto_scaling_rule(
        self, action: ModifyEndpointAutoScalingRuleAction
    ) -> ModifyEndpointAutoScalingRuleActionResult:
        try:
            _rule_id = RuleId(action.id)
        except ValueError:
            raise EndpointAutoScalingRuleNotFound

        async with self._db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointAutoScalingRuleRow.get(db_session, _rule_id, load_endpoint=True)
            except NoResultFound:
                raise EndpointAutoScalingRuleNotFound

            match action.requester_ctx.user_role:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.endpoint_row.domain != action.requester_ctx.domain_name:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.endpoint_row.created_user != action.requester_ctx.user_id:
                        raise GenericForbidden

            async def _do_mutate() -> MutationResult:
                if (_newval := action.threshold) and _newval.state() == State.UPDATE:
                    try:
                        row.threshold = decimal.Decimal(cast(str, _newval.value()))
                    except decimal.InvalidOperation:
                        raise InvalidAPIParameters(f"Cannot convert {_newval} to Decimal")

                action.metric_source.set_attr(row)
                action.metric_name.set_attr(row)
                action.comparator.set_attr(row)
                action.step_size.set_attr(row)
                action.cooldown_seconds.set_attr(row)
                action.min_replicas.set_attr(row)
                action.max_replicas.set_attr(row)

                return MutationResult(
                    success=True,
                    message="Auto scaling rule updated",
                    data=row,
                )

            res = await self._db_mutation_wrapper(_do_mutate)

            return ModifyEndpointAutoScalingRuleActionResult(
                success=res.success,
                data=EndpointAutoScalingRuleData.from_row(res.data),
            )

    async def delete_endpoint_auto_scaling_rule(
        self, action: DeleteEndpointAutoScalingRuleAction
    ) -> DeleteEndpointAutoScalingRuleActionResult:
        try:
            _rule_id = RuleId(action.id)
        except ValueError:
            raise EndpointAutoScalingRuleNotFound

        async with self._db.begin_session(commit_on_end=True) as db_session:
            try:
                row = await EndpointAutoScalingRuleRow.get(db_session, _rule_id, load_endpoint=True)
            except NoResultFound:
                raise EndpointAutoScalingRuleNotFound

            match action.requester_ctx.user_role:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    if row.endpoint_row.domain != action.requester_ctx.domain_name:
                        raise GenericForbidden
                case UserRole.USER:
                    if row.endpoint_row.created_user != action.requester_ctx.user_id:
                        raise GenericForbidden

            async def _do_mutate() -> MutationResult:
                await db_session.delete(row)
                return MutationResult(
                    success=True,
                    message="Auto scaling rule removed",
                    data=None,
                )

            res = await self._db_mutation_wrapper(_do_mutate)

            return DeleteEndpointAutoScalingRuleActionResult(
                success=res.success,
            )

    async def _db_mutation_wrapper(
        self, _do_mutate: Callable[[], Awaitable[MutationResult]]
    ) -> MutationResult:
        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
            return MutationResult(success=False, message=f"integrity error: {e}", data=None)
        except sa.exc.StatementError as e:
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
