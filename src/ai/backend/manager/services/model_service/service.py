import asyncio
import logging
import secrets
import uuid

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
from ai.backend.common.types import AgentId, ImageAlias, SessionTypes
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow, EndpointTokenRow
from ai.backend.manager.models.group import resolve_group_name_or_id
from ai.backend.manager.models.image import ImageIdentifier, ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.routing import RouteStatus, RoutingRow
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session import KernelLoadingStrategy, SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.model_service.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_service.actions.create_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
    ServiceInfo,
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
    GenericForbidden,
    InvalidAPIParameters,
    ModelServiceNotFound,
)
from ai.backend.manager.services.model_service.types import (
    CompactServiceInfo,
    ErrorInfo,
    RequesterCtx,
    RouteInfo,
)
from ai.backend.manager.types import UserScope
from ai.backend.manager.utils import check_if_requester_is_eligible_to_act_as_target_user_uuid

log = BraceStyleAdapter(logging.getLogger(__name__))


class ModelService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry
    _background_task_manager: BackgroundTaskManager
    _event_dispatcher: EventDispatcher

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        agent_registry: AgentRegistry,
        background_task_manager: BackgroundTaskManager,
        event_dispatcher: EventDispatcher,
    ) -> None:
        self._db = db
        self._registry = agent_registry
        self._background_task_manager = background_task_manager
        self._event_dispatcher = event_dispatcher

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
