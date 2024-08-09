import asyncio
import json
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Iterable, Sequence, Tuple

import aiohttp
import aiohttp_cors
import aiotools
import attrs
import sqlalchemy as sa
from aiohttp import web
from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    Field,
    HttpUrl,
    NonNegativeFloat,
    NonNegativeInt,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import NoResultFound
from yarl import URL

from ai.backend.common import typed_validators as tv
from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.docker import ImageRef
from ai.backend.common.events import (
    EventHandler,
    KernelLifecycleEventReason,
    ModelServiceStatusEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionPreparingEvent,
    SessionStartedEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AccessKey,
    AgentId,
    ClusterMode,
    ImageAlias,
    RuntimeVariant,
    SessionTypes,
    VFolderMount,
    VFolderUsageMode,
)

from ..defs import DEFAULT_IMAGE_ARCH
from ..models import (
    EndpointLifecycle,
    EndpointRow,
    EndpointTokenRow,
    ImageRow,
    KernelLoadingStrategy,
    KeyPairRow,
    ModelServicePredicateChecker,
    RouteStatus,
    RoutingRow,
    SessionRow,
    UserRole,
    UserRow,
    query_accessible_vfolders,
    resolve_group_name_or_id,
    scaling_groups,
    vfolders,
)
from ..types import MountOptionModel, UserScope
from .auth import auth_required
from .exceptions import InvalidAPIParameters, ObjectNotFound, VFolderNotFound
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .session import query_userinfo
from .types import CORSOptions, WebMiddleware
from .utils import (
    BaseResponseModel,
    get_access_key_scopes,
    get_user_uuid_scopes,
    pydantic_params_api_handler,
    pydantic_response_api_handler,
    undefined,
)

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))


async def is_user_allowed_to_access_resource(
    db_sess: AsyncSession,
    request: web.Request,
    resource_owner: uuid.UUID,
) -> bool:
    if request["user"]["is_superadmin"]:
        return True
    elif request["user"]["is_admin"]:
        query = sa.select(UserRow).filter(UserRow.uuid == resource_owner)
        result = await db_sess.execute(query)
        user = result.scalar()
        return user.domain_name == request["user"]["domain_name"]
    else:
        return request["user"]["uyud"] == resource_owner


class ListServeRequestModel(BaseModel):
    name: str | None = Field(default=None)


class SuccessResponseModel(BaseResponseModel):
    success: bool = Field(default=True)


class CompactServeInfoModel(BaseModel):
    id: uuid.UUID = Field(description="Unique ID referencing the model service.")
    name: str = Field(description="Name of the model service.")
    desired_session_count: NonNegativeInt = Field(
        description="Number of identical inference sessions."
    )
    active_route_count: NonNegativeInt = Field(
        description=(
            "Information of routes which are actually spawned and ready to accept the traffic."
        )
    )
    service_endpoint: HttpUrl | None = Field(
        default=None,
        description=(
            "HTTP(S) endpoint to the API service. This field will be filed after the attempt to"
            " create a first inference session succeeds. Endpoint created is fixed and immutable"
            " for the bound endpoint until the endpoint is destroyed."
        ),
    )
    is_public: bool = Field(
        description=(
            'Indicates if the API endpoint is open to public. In this context "public" means there'
            " will be no authentication required to communicate with this API service."
        )
    )


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(ListServeRequestModel)
async def list_serve(
    request: web.Request, params: ListServeRequestModel
) -> list[CompactServeInfoModel]:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]

    log.info("SERVE.LIST (email:{}, ak:{})", request["user"]["email"], access_key)
    query_conds = (EndpointRow.session_owner == request["user"]["uuid"]) & (
        EndpointRow.lifecycle_stage == EndpointLifecycle.CREATED
    )
    if params.name:
        query_conds &= EndpointRow.name == params.name

    async with root_ctx.db.begin_readonly_session() as db_sess:
        query = (
            sa.select(EndpointRow).where(query_conds).options(selectinload(EndpointRow.routings))
        )
        result = await db_sess.execute(query)
        rows = result.scalars().all()

    return [
        CompactServeInfoModel(
            id=endpoint.id,
            name=endpoint.name,
            desired_session_count=endpoint.desired_session_count,
            active_route_count=len([
                r for r in endpoint.routings if r.status == RouteStatus.HEALTHY
            ]),
            service_endpoint=endpoint.url,
            is_public=endpoint.open_to_public,
        )
        for endpoint in rows
    ]


class RouteInfoModel(BaseModel):
    route_id: uuid.UUID = Field(
        description=(
            "Unique ID referencing endpoint route. Each endpoint route has a one-to-one"
            " relationship with the inference session."
        )
    )
    session_id: uuid.UUID = Field(description="Unique ID referencing the inference session.")
    traffic_ratio: NonNegativeFloat


class ServeInfoModel(BaseResponseModel):
    endpoint_id: uuid.UUID = Field(description="Unique ID referencing the model service.")
    model_id: Annotated[uuid.UUID, Field(description="ID of model VFolder.")]
    extra_mounts: Annotated[
        Sequence[uuid.UUID],
        Field(description="List of extra VFolders which will be mounted to model service session."),
    ]
    name: str = Field(description="Name of the model service.")
    desired_session_count: NonNegativeInt = Field(
        description="Number of identical inference sessions."
    )
    model_definition_path: str | None = Field(
        description="Path to the the model definition file. If not set, Backend.AI will look for model-definition.yml or model-definition.yaml by default."
    )
    active_routes: list[RouteInfoModel] = Field(
        description="Information of routes which are bound with healthy sessions."
    )
    service_endpoint: HttpUrl | None = Field(
        default=None,
        description=(
            "HTTP(S) endpoint to the API service. This field will be filed after the attempt to"
            " create a first inference session succeeds. Endpoint created is fixed and immutable"
            " for the bound endpoint until the endpoint is destroyed."
        ),
    )
    is_public: bool = Field(
        description=(
            'Indicates if the API endpoint is open to public. In this context "public" means there'
            " will be no authentication required to communicate with this API service."
        )
    )
    runtime_variant: Annotated[
        RuntimeVariant,
        Field(description="Type of the inference runtime the image will try to load."),
    ]


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def get_info(request: web.Request) -> ServeInfoModel:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.GET_INFO (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound

    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    return ServeInfoModel(
        endpoint_id=endpoint.id,
        model_id=endpoint.model,
        extra_mounts=[m.vfid.folder_id for m in endpoint.extra_mounts],
        name=endpoint.name,
        model_definition_path=endpoint.model_definition_path,
        desired_session_count=endpoint.desired_session_count,
        active_routes=[
            RouteInfoModel(route_id=r.id, session_id=r.session, traffic_ratio=r.traffic_ratio)
            for r in endpoint.routings
            if r.status == RouteStatus.HEALTHY
        ],
        service_endpoint=endpoint.url,
        is_public=endpoint.open_to_public,
        runtime_variant=endpoint.runtime_variant,
    )


class ServiceConfigModel(BaseModel):
    model: str = Field(description="Name or ID of the model VFolder", examples=["ResNet50"])
    model_definition_path: str | None = Field(
        description="Path to the model definition file. If not set, Backend.AI will look for model-definition.yml or model-definition.yaml by default.",
        default=None,
    )
    model_version: int = Field(
        validation_alias=AliasChoices("model_version", "modelVersion"),
        description="Unused; Reserved for future works",
        default=1,
    )
    model_mount_destination: str = Field(
        validation_alias=AliasChoices("model_mount_destination", "modelMountDestination"),
        default="/models",
        description=(
            "Mount destination for the model VFolder will be mounted inside the inference session. Must be set to `/models` when choosing `runtime_variant` other than `CUSTOM` or `CMD`."
        ),
    )

    extra_mounts: Annotated[
        dict[uuid.UUID, MountOptionModel],
        Field(
            description=(
                "Specifications about extra VFolders mounted to model service session. "
                "MODEL type VFolders are not allowed to be attached to model service session with this option."
            ),
            default={},
        ),
    ]

    environ: dict[str, str] | None = Field(
        description="Environment variables to be set inside the inference session",
        default=None,
    )
    scaling_group: str = Field(
        validation_alias=AliasChoices("scaling_group", "scalingGroup"),
        description="Name of the resource group to spawn inference sessions",
        examples=["nvidia-H100"],
    )
    resources: dict[str, str | int] = Field(examples=[{"cpu": 4, "mem": "32g", "cuda.shares": 2.5}])
    resource_opts: dict[str, str | int] = Field(examples=[{"shmem": "2g"}], default={})


class NewServiceRequestModel(BaseModel):
    service_name: tv.SessionName = Field(
        validation_alias=AliasChoices("name", "service_name", "clientSessionToken"),
        description="Name of the service",
    )
    desired_session_count: int = Field(
        validation_alias=AliasChoices("desired_session_count", "desiredSessionCount"),
        description="Number of sessions to serve traffic",
    )
    image: str = Field(
        validation_alias=AliasChoices("image", "lang"),
        description="String reference of the image which will be used to create session",
        examples=["cr.backend.ai/stable/python-tensorflow:2.7-py38-cuda11.3"],
    )
    runtime_variant: Annotated[
        RuntimeVariant,
        Field(
            description="Type of the inference runtime the image will try to load.",
            default=RuntimeVariant.CUSTOM,
        ),
    ]
    architecture: str = Field(
        validation_alias=AliasChoices("arch", "architecture"),
        description="Image architecture",
        default=DEFAULT_IMAGE_ARCH,
    )
    group: str = Field(
        validation_alias=AliasChoices("group", "groupName", "group_name"),
        description="Name of project to spawn session",
        default="default",
    )
    domain: str = Field(
        validation_alias=AliasChoices("domain", "domainName", "domain_name"),
        description="Name of domain to spawn session",
        default="default",
    )
    cluster_size: int = Field(
        validation_alias=AliasChoices("cluster_size", "clusterSize"), default=1
    )
    cluster_mode: ClusterMode = Field(
        validation_alias=AliasChoices("cluster_mode", "clusterMode"),
        default=ClusterMode.SINGLE_NODE,
    )
    tag: str | None = Field(default=None)
    startup_command: str | None = Field(
        validation_alias=AliasChoices("startup_command", "startupCommand"),
        default=None,
    )
    bootstrap_script: str | None = Field(
        validation_alias=AliasChoices("bootstrap_script", "bootstrapScript"),
        default=None,
    )
    callback_url: AnyUrl | None = Field(
        validation_alias=AliasChoices("callback_url", "callbackUrl", "CallbackURL"),
        default=None,
    )
    owner_access_key: str | None = Field(
        description=(
            "(for privileged users only) when specified, transfer ownership of the inference"
            " session to specified user"
        ),
        default=None,
    )
    open_to_public: bool = Field(
        description="If set to true, do not require an API key to access the model service",
        default=False,
    )
    config: ServiceConfigModel


@dataclass
class ValidationResult:
    model_id: uuid.UUID
    model_definition_path: str | None
    requester_access_key: AccessKey
    owner_access_key: AccessKey
    owner_uuid: uuid.UUID
    owner_role: UserRole
    group_id: uuid.UUID
    resource_policy: dict
    scaling_group: str
    extra_mounts: Sequence[VFolderMount]


async def _validate(request: web.Request, params: NewServiceRequestModel) -> ValidationResult:
    root_ctx: RootContext = request.app["_root.context"]
    scopes_param = {
        "owner_access_key": (
            None if params.owner_access_key is undefined else params.owner_access_key
        ),
    }

    requester_access_key, owner_access_key = await get_access_key_scopes(request, scopes_param)
    if params.desired_session_count > (
        _m := request["user"]["resource_policy"]["max_session_count_per_model_session"]
    ):
        raise InvalidAPIParameters(f"Cannot spawn more than {_m} sessions for a single service")

    async with root_ctx.db.begin_readonly() as conn:
        checked_scaling_group = await ModelServicePredicateChecker.check_scaling_group(
            conn,
            params.config.scaling_group,
            owner_access_key,
            params.domain,
            params.group,
        )

        params.config.scaling_group = checked_scaling_group

        owner_uuid, group_id, resource_policy = await query_userinfo(
            request, params.model_dump(), conn
        )
        query = sa.select([UserRow.role]).where(UserRow.uuid == owner_uuid)
        owner_role = (await conn.execute(query)).scalar()
        assert owner_role

        allowed_vfolder_types = await root_ctx.shared_config.get_vfolder_types()
        try:
            extra_vf_conds = vfolders.c.id == uuid.UUID(params.config.model)
            matched_vfolders = await query_accessible_vfolders(
                conn,
                owner_uuid,
                user_role=owner_role,
                domain_name=params.domain,
                allowed_vfolder_types=allowed_vfolder_types,
                extra_vf_conds=extra_vf_conds,
            )
        except Exception as e:
            # just catching ValueError | VFolderNotFound will raise
            # TypeError: catching classes that do not inherit from BaseException is not allowed
            if isinstance(e, ValueError) or isinstance(e, VFolderNotFound):
                try:
                    extra_vf_conds = (vfolders.c.name == params.config.model) & (
                        vfolders.c.usage_mode == VFolderUsageMode.MODEL
                    )
                    matched_vfolders = await query_accessible_vfolders(
                        conn,
                        owner_uuid,
                        user_role=owner_role,
                        domain_name=params.domain,
                        allowed_vfolder_types=allowed_vfolder_types,
                        extra_vf_conds=extra_vf_conds,
                    )
                except VFolderNotFound as e:
                    raise VFolderNotFound("Cannot find model folder") from e
            else:
                raise
        if len(matched_vfolders) == 0:
            raise VFolderNotFound
        folder_row = matched_vfolders[0]
        if folder_row["usage_mode"] != VFolderUsageMode.MODEL:
            raise InvalidAPIParameters("Selected VFolder is not a model folder")

        model_id = folder_row["id"]

        vfolder_mounts = await ModelServicePredicateChecker.check_extra_mounts(
            conn,
            root_ctx.shared_config,
            root_ctx.storage_manager,
            model_id,
            params.config.model_mount_destination,
            params.config.extra_mounts,
            UserScope(
                domain_name=params.domain,
                group_id=group_id,
                user_uuid=owner_uuid,
                user_role=owner_role,
            ),
            resource_policy,
        )

    if params.runtime_variant == RuntimeVariant.CUSTOM:
        yaml_path = await ModelServicePredicateChecker.validate_model_definition(
            root_ctx.storage_manager,
            folder_row,
            params.config.model_definition_path,
        )
    else:
        if (
            params.runtime_variant != RuntimeVariant.CMD
            and params.config.model_mount_destination != "/models"
        ):
            raise InvalidAPIParameters(
                "Model mount destination must be /models for non-custom runtimes"
            )
        # this path won't be used on actual session but just to keep the convention
        yaml_path = "model-definition.yaml"

    return ValidationResult(
        model_id,
        yaml_path,
        requester_access_key,
        owner_access_key,
        owner_uuid,
        owner_role,
        group_id,
        resource_policy,
        checked_scaling_group,
        vfolder_mounts,
    )


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(NewServiceRequestModel)
async def create(request: web.Request, params: NewServiceRequestModel) -> ServeInfoModel:
    """
    Creates a new model service. If `desired_session_count` is greater than zero,
    then inference sessions will be automatically scheduled upon successful creation of model service.
    """
    root_ctx: RootContext = request.app["_root.context"]

    validation_result = await _validate(request, params)

    async with root_ctx.db.begin_readonly_session() as session:
        image_row = await ImageRow.resolve(
            session,
            [
                ImageRef(params.image, ["*"], params.architecture),
                ImageAlias(params.image),
            ],
        )

    creation_config = params.config.model_dump()
    creation_config["mounts"] = [
        validation_result.model_id,
        *[m.vfid.folder_id for m in validation_result.extra_mounts],
    ]
    creation_config["mount_map"] = {
        validation_result.model_id: params.config.model_mount_destination,
        **{m.vfid.folder_id: m.kernel_path.as_posix() for m in validation_result.extra_mounts},
    }
    creation_config["mount_options"] = {
        m.vfid.folder_id: {"permission": m.mount_perm} for m in validation_result.extra_mounts
    }
    sudo_session_enabled = request["user"]["sudo_session_enabled"]

    # check if session is valid to be created
    await root_ctx.registry.create_session(
        "",
        params.image,
        params.architecture,
        UserScope(
            domain_name=params.domain,
            group_id=validation_result.group_id,
            user_uuid=validation_result.owner_uuid,
            user_role=validation_result.owner_role,
        ),
        validation_result.owner_access_key,
        validation_result.resource_policy,
        SessionTypes.INFERENCE,
        creation_config,
        params.cluster_mode,
        params.cluster_size,
        dry_run=True,  # Setting this to True will prevent actual session from being enqueued
        bootstrap_script=params.bootstrap_script,
        startup_command=params.startup_command,
        tag=params.tag,
        callback_url=URL(params.callback_url.unicode_string()) if params.callback_url else None,
        sudo_session_enabled=sudo_session_enabled,
    )

    async with root_ctx.db.begin_session() as db_sess:
        query = sa.select(EndpointRow).where(
            (EndpointRow.lifecycle_stage != EndpointLifecycle.DESTROYED)
            & (EndpointRow.name == params.service_name)
        )
        result = await db_sess.execute(query)
        service_with_duplicate_name = result.scalar()
        if service_with_duplicate_name is not None:
            raise InvalidAPIParameters("Cannot create multiple services with same name")

        project_id = await resolve_group_name_or_id(
            await db_sess.connection(), params.domain, params.group
        )
        if project_id is None:
            raise InvalidAPIParameters(f"Invalid group name {project_id}")
        endpoint = EndpointRow(
            params.service_name,
            validation_result.model_definition_path,
            request["user"]["uuid"],
            validation_result.owner_uuid,
            params.desired_session_count,
            image_row,
            validation_result.model_id,
            params.domain,
            project_id,
            validation_result.scaling_group,
            params.config.resources,
            params.cluster_mode,
            params.cluster_size,
            validation_result.extra_mounts,
            model_mount_destination=params.config.model_mount_destination,
            tag=params.tag,
            startup_command=params.startup_command,
            callback_url=URL(params.callback_url.unicode_string()) if params.callback_url else None,
            environ=params.config.environ,
            bootstrap_script=params.bootstrap_script,
            resource_opts=params.config.resource_opts,
            open_to_public=params.open_to_public,
            runtime_variant=params.runtime_variant,
        )
        db_sess.add(endpoint)
        await db_sess.flush()
        endpoint_id = endpoint.id

    return ServeInfoModel(
        endpoint_id=endpoint_id,
        model_id=endpoint.model,
        extra_mounts=[m.vfid.folder_id for m in endpoint.extra_mounts],
        name=params.service_name,
        model_definition_path=validation_result.model_definition_path,
        desired_session_count=params.desired_session_count,
        active_routes=[],
        service_endpoint=None,
        is_public=params.open_to_public,
        runtime_variant=params.runtime_variant,
    )


class TryStartResponseModel(BaseModel):
    task_id: str


@auth_required
@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(NewServiceRequestModel)
async def try_start(request: web.Request, params: NewServiceRequestModel) -> TryStartResponseModel:
    root_ctx: RootContext = request.app["_root.context"]
    background_task_manager = root_ctx.background_task_manager

    validation_result = await _validate(request, params)

    async with root_ctx.db.begin_readonly_session() as session:
        image_row = await ImageRow.resolve(
            session,
            [
                ImageRef(params.image, ["*"], params.architecture),
                ImageAlias(params.image),
            ],
        )
        query = sa.select(sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)).where(
            UserRow.uuid == request["user"]["uuid"]
        )
        created_user = (await session.execute(query)).fetchone()

    creation_config = params.config.model_dump()
    creation_config["mount_map"] = {
        validation_result.model_id: params.config.model_mount_destination
    }
    sudo_session_enabled = request["user"]["sudo_session_enabled"]

    async def _task(reporter: ProgressReporter) -> None:
        terminated_event = asyncio.Event()

        result = await root_ctx.registry.create_session(
            f"model-eval-{secrets.token_urlsafe(16)}",
            image_row.name,
            image_row.architecture,
            UserScope(
                domain_name=params.domain,
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
                    validation_result.model_id: params.config.model_mount_destination,
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
            params.cluster_mode,
            params.cluster_size,
            bootstrap_script=params.bootstrap_script,
            startup_command=params.startup_command,
            tag=params.tag,
            callback_url=URL(params.callback_url.unicode_string()) if params.callback_url else None,
            enqueue_only=True,
            sudo_session_enabled=sudo_session_enabled,
        )

        await reporter.update(
            message=json.dumps({
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
            await reporter.update(message=json.dumps(task_message))

            match event:
                case SessionTerminatedEvent() | SessionCancelledEvent():
                    terminated_event.set()
                case ModelServiceStatusEvent():
                    async with root_ctx.db.begin_readonly_session() as db_sess:
                        session = await SessionRow.get_session(
                            db_sess,
                            result["sessionId"],
                            None,
                            kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                        )
                        await root_ctx.registry.destroy_session(
                            session,
                            forced=True,
                        )

        session_event_matcher = lambda args: args[0] == str(result["sessionId"])
        model_service_event_matcher = lambda args: args[1] == str(result["sessionId"])

        handlers: list[EventHandler] = [
            root_ctx.event_dispatcher.subscribe(
                SessionPreparingEvent,
                None,
                _handle_event,
                args_matcher=session_event_matcher,
            ),
            root_ctx.event_dispatcher.subscribe(
                SessionStartedEvent,
                None,
                _handle_event,
                args_matcher=session_event_matcher,
            ),
            root_ctx.event_dispatcher.subscribe(
                SessionCancelledEvent,
                None,
                _handle_event,
                args_matcher=session_event_matcher,
            ),
            root_ctx.event_dispatcher.subscribe(
                SessionTerminatedEvent,
                None,
                _handle_event,
                args_matcher=session_event_matcher,
            ),
            root_ctx.event_dispatcher.subscribe(
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
                root_ctx.event_dispatcher.unsubscribe(handler)

    task_id = await background_task_manager.start(_task)
    return TryStartResponseModel(task_id=str(task_id))


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def delete(request: web.Request) -> SuccessResponseModel:
    """
    Removes model service (and inference sessions for the service also).
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.DELETE (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    async with root_ctx.db.begin_session() as db_sess:
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
                    "desired_session_count": 0,
                    "lifecycle_stage": EndpointLifecycle.DESTROYING,
                })
            )
        await db_sess.execute(query)
    return SuccessResponseModel()


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def sync(request: web.Request) -> SuccessResponseModel:
    """
    Force syncs up-to-date model service information with AppProxy.
    In normal situations this will be automatically handled by Backend.AI schedulers,
    but this API is left open in case of unexpected restart of AppProxy process.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info("SERVE.SYNC (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id)

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    async with root_ctx.db.begin_session() as db_sess:
        await root_ctx.registry.update_appproxy_endpoint_routes(
            db_sess, endpoint, [r for r in endpoint.routings if r.status == RouteStatus.HEALTHY]
        )
    return SuccessResponseModel()


class ScaleRequestModel(BaseModel):
    to: int = Field(description="Ideal number of inference sessions")


class ScaleResponseModel(BaseResponseModel):
    current_route_count: int
    target_count: int


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(ScaleRequestModel)
async def scale(request: web.Request, params: ScaleRequestModel) -> ScaleResponseModel:
    """
    Updates ideal inference session count manually. Based on the difference of this number,
    inference sessions will be created or removed automatically.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.SCALE (email:{}, ak:{}, s:{})", request["user"]["email"], access_key, service_id
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    if params.to < 0:
        raise InvalidAPIParameters("Amount of desired session count cannot be a negative number")
    elif params.to > (
        _m := request["user"]["resource_policy"]["max_session_count_per_model_session"]
    ):
        raise InvalidAPIParameters(f"Cannot spawn more than {_m} sessions for a single service")

    async with root_ctx.db.begin_session() as db_sess:
        query = (
            sa.update(EndpointRow)
            .where(EndpointRow.id == service_id)
            .values({"desired_session_count": params.to})
        )
        await db_sess.execute(query)
        return ScaleResponseModel(
            current_route_count=len(endpoint.routings), target_count=params.to
        )


class UpdateRouteRequestModel(BaseModel):
    traffic_ratio: NonNegativeFloat


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(UpdateRouteRequestModel)
async def update_route(
    request: web.Request, params: UpdateRouteRequestModel
) -> SuccessResponseModel:
    """
    Updates traffic bias of specific route.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])
    route_id = uuid.UUID(request.match_info["route_id"])

    log.info(
        "SERVE.UPDATE_ROUTE (email:{}, ak:{}, s:{}, r:{})",
        request["user"]["email"],
        access_key,
        service_id,
        route_id,
    )

    async with root_ctx.db.begin_session() as db_sess:
        try:
            route = await RoutingRow.get(db_sess, route_id, load_endpoint=True)
        except NoResultFound:
            raise ObjectNotFound
        if route.endpoint != service_id:
            raise ObjectNotFound
        await get_user_uuid_scopes(request, {"owner_uuid": route.endpoint_row.session_owner})

        query = (
            sa.update(RoutingRow)
            .where(RoutingRow.id == route_id)
            .values({"traffic_ratio": params.traffic_ratio})
        )
        await db_sess.execute(query)
        endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        try:
            await root_ctx.registry.update_appproxy_endpoint_routes(
                db_sess, endpoint, [r for r in endpoint.routes if r.status == RouteStatus.HEALTHY]
            )
        except aiohttp.ClientError as e:
            log.warning("failed to communicate with AppProxy endpoint: {}", str(e))
        return SuccessResponseModel()


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def delete_route(request: web.Request) -> SuccessResponseModel:
    """
    Scales down the service by removing specific inference session.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])
    route_id = uuid.UUID(request.match_info["route_id"])

    log.info(
        "SERVE.DELETE_ROUTE (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )
    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            route = await RoutingRow.get(db_sess, route_id, load_session=True)
        except NoResultFound:
            raise ObjectNotFound
        if route.endpoint != service_id:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": route.endpoint_row.session_owner})
    if route.status == RouteStatus.PROVISIONING:
        raise InvalidAPIParameters("Cannot remove route in PROVISIONING status")

    await root_ctx.registry.destroy_session(
        route.session_row,
        forced=False,
        reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN,
    )

    async with root_ctx.db.begin_session() as db_sess:
        query = (
            sa.update(EndpointRow)
            .where(EndpointRow.id == service_id)
            .values({"desired_session_count": route.endpoint_row.desired_session_count - 1})
        )
        await db_sess.execute(query)
        return SuccessResponseModel()


class TokenRequestModel(BaseModel):
    duration: tv.TimeDuration = Field(default=None, description="duration of the token.")
    valid_until: int | None = Field(
        default=None, description="Absolute token expiry date, expressed in Unix epoch format."
    )


class TokenResponseModel(BaseResponseModel):
    token: str


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_params_api_handler(TokenRequestModel)
async def generate_token(request: web.Request, params: TokenRequestModel) -> TokenResponseModel:
    """
    Generates a token which acts as an API key to authenticate when calling model service endpoint.
    If both duration and valid_until is not set then the AppProxy will determine appropriate lifetime of the token.
    duration and valid_until can't be both specified.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.GENERATE_TOKEN (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
        query = (
            sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == endpoint.resource_group))
        )

        result = await db_sess.execute(query)
        sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        wsproxy_api_token = sgroup["wsproxy_api_token"]

    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    if params.valid_until:
        exp = params.valid_until
    elif params.duration:
        exp = int((datetime.now() + params.duration).timestamp())
    else:
        raise InvalidAPIParameters("valid_until and duration can't be both unspecified")
    if datetime.now().timestamp() > exp:
        raise InvalidAPIParameters("valid_until is older than now")
    body = {"user_uuid": str(endpoint.session_owner), "exp": exp}
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

    async with root_ctx.db.begin_session() as db_sess:
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
        return TokenResponseModel(token=token)


class ErrorInfoModel(BaseModel):
    session_id: uuid.UUID | None
    error: dict[str, Any]


class ErrorListResponseModel(BaseResponseModel):
    errors: list[ErrorInfoModel]
    retries: int


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def list_errors(request: web.Request) -> ErrorListResponseModel:
    """
    List errors raised while trying to create the inference sessions. Backend.AI will
    stop trying to create an inference session for the model service if six (6) error stacks
    up. The only way to clear the error and retry spawning session is to call
    `clear_error` (POST /services/{service_id}/errors/clear) API.
    """
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.LIST_ERRORS (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    error_routes = [r for r in endpoint.routings if r.status == RouteStatus.FAILED_TO_START]

    return ErrorListResponseModel(
        errors=[
            ErrorInfoModel(
                session_id=route.error_data.get("session_id"), error=route.error_data["errors"]
            )
            for route in error_routes
        ],
        retries=endpoint.retries,
    )


@auth_required
@server_status_required(READ_ALLOWED)
async def clear_error(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    access_key = request["keypair"]["access_key"]
    service_id = uuid.UUID(request.match_info["service_id"])

    log.info(
        "SERVE.CLEAR_ERROR (email:{}, ak:{}, s:{})",
        request["user"]["email"],
        access_key,
        service_id,
    )

    async with root_ctx.db.begin_readonly_session() as db_sess:
        try:
            endpoint = await EndpointRow.get(db_sess, service_id, load_routes=True)
        except NoResultFound:
            raise ObjectNotFound
    await get_user_uuid_scopes(request, {"owner_uuid": endpoint.session_owner})

    async with root_ctx.db.begin_session() as db_sess:
        query = sa.delete(RoutingRow).where(
            (RoutingRow.endpoint == service_id) & (RoutingRow.status == RouteStatus.FAILED_TO_START)
        )
        await db_sess.execute(query)
        query = sa.update(EndpointRow).values({"retries": 0}).where(EndpointRow.id == endpoint.id)
        await db_sess.execute(query)

    return web.Response(status=204)


class RuntimeInfo(BaseModel):
    name: Annotated[str, Field(description="Identifier to be passed later inside request body")]
    human_readable_name: Annotated[
        str, Field(description="Use this value as displayed label to user")
    ]


class RuntimeInfoModel(BaseModel):
    runtimes: list[RuntimeInfo]


@auth_required
@server_status_required(READ_ALLOWED)
@pydantic_response_api_handler
async def list_supported_runtimes(request: web.Request) -> RuntimeInfoModel:
    return RuntimeInfoModel(
        runtimes=[
            RuntimeInfo(name=v.value, human_readable_name=MODEL_SERVICE_RUNTIME_PROFILES[v].name)
            for v in RuntimeVariant
        ]
    )


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    database_ptask_group: aiotools.PersistentTaskGroup


async def init(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    app_ctx.database_ptask_group = aiotools.PersistentTaskGroup()


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["services.context"]
    await app_ctx.database_ptask_group.shutdown()


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "services"
    app["api_versions"] = (4, 5)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["services.context"] = PrivateContext()
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_serve))
    cors.add(root_resource.add_route("POST", create))
    cors.add(add_route("POST", "/_/try", try_start))
    cors.add(add_route("GET", "/_/runtimes", list_supported_runtimes))
    cors.add(add_route("GET", "/{service_id}", get_info))
    cors.add(add_route("DELETE", "/{service_id}", delete))
    cors.add(add_route("GET", "/{service_id}/errors", list_errors))
    cors.add(add_route("POST", "/{service_id}/errors/clear", clear_error))
    cors.add(add_route("POST", "/{service_id}/scale", scale))
    cors.add(add_route("POST", "/{service_id}/sync", sync))
    cors.add(add_route("PUT", "/{service_id}/routings/{route_id}", update_route))
    cors.add(add_route("DELETE", "/{service_id}/routings/{route_id}", delete_route))
    cors.add(add_route("POST", "/{service_id}/token", generate_token))
    return app, []
