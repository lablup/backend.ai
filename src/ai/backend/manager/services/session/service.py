import asyncio
import base64
import functools
import logging
import secrets
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Union, cast
from urllib.parse import urlparse

import aiohttp
import aiotools
import multidict
import sqlalchemy as sa
import trafaret as t
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload, selectinload

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.docker import DEFAULT_KERNEL_FEATURE, ImageRef, KernelFeatures, LabelName
from ai.backend.common.events.bgtask import (
    BaseBgtaskDoneEvent,
)
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.events.hub.propagators.bgtask import BgtaskPropagator
from ai.backend.common.events.types import (
    EventDomain,
)
from ai.backend.common.exception import (
    BackendAIError,
    BgtaskCancelledError,
    BgtaskFailedError,
    InvalidAPIParameters,
    UnknownImageReference,
)
from ai.backend.common.json import load_json
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.common.types import (
    AccessKey,
    ImageAlias,
    ImageRegistry,
    SessionId,
    SessionTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.scaling_group import query_wsproxy_status
from ai.backend.manager.api.session import (
    CustomizedImageVisibilityScope,
    drop_undefined,
    find_dependency_sessions,
    find_dependent_sessions,
    overwritten_param_check,
)
from ai.backend.manager.api.utils import undefined
from ai.backend.manager.errors.exceptions import (
    AppNotFound,
    GenericForbidden,
    InternalServerError,
    QuotaExceeded,
    ServiceUnavailable,
    SessionAlreadyExists,
    SessionNotFound,
    TaskTemplateNotFound,
    TooManySessionsMatched,
    UnknownImageReferenceError,
)
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow, groups
from ai.backend.manager.models.image import ImageIdentifier, ImageRow, rescan_images
from ai.backend.manager.models.kernel import (
    KernelRow,
)
from ai.backend.manager.models.scaling_group import scaling_groups
from ai.backend.manager.models.session import (
    DEAD_SESSION_STATUSES,
    PRIVATE_SESSION_TYPES,
    KernelLoadingStrategy,
    SessionRow,
    SessionStatus,
)
from ai.backend.manager.models.session_template import session_templates
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_txn_retry
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusAction,
    CheckAndTransitStatusActionResult,
    CheckAndTransitStatusBatchAction,
    CheckAndTransitStatusBatchActionResult,
)
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
    CommitSessionActionResult,
)
from ai.backend.manager.services.session.actions.complete import (
    CompleteAction,
    CompleteActionResult,
)
from ai.backend.manager.services.session.actions.convert_session_to_image import (
    ConvertSessionToImageAction,
    ConvertSessionToImageActionResult,
)
from ai.backend.manager.services.session.actions.create_cluster import (
    CreateClusterAction,
    CreateClusterActionResult,
)
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionResult,
)
from ai.backend.manager.services.session.actions.create_from_template import (
    CreateFromTemplateAction,
    CreateFromTemplateActionResult,
)
from ai.backend.manager.services.session.actions.destory_session import (
    DestroySessionAction,
    DestroySessionActionResult,
)
from ai.backend.manager.services.session.actions.download_file import (
    DownloadFileAction,
    DownloadFileActionResult,
)
from ai.backend.manager.services.session.actions.download_files import (
    DownloadFilesAction,
    DownloadFilesActionResult,
)
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionResult,
)
from ai.backend.manager.services.session.actions.get_abusing_report import (
    GetAbusingReportAction,
    GetAbusingReportActionResult,
)
from ai.backend.manager.services.session.actions.get_commit_status import (
    GetCommitStatusAction,
    GetCommitStatusActionResult,
)
from ai.backend.manager.services.session.actions.get_container_logs import (
    GetContainerLogsAction,
    GetContainerLogsActionResult,
)
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
    GetDependencyGraphActionResult,
)
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
    GetDirectAccessInfoActionResult,
)
from ai.backend.manager.services.session.actions.get_session_info import (
    GetSessionInfoAction,
    GetSessionInfoActionResult,
)
from ai.backend.manager.services.session.actions.interrupt_session import (
    InterruptSessionAction,
    InterruptSessionActionResult,
)
from ai.backend.manager.services.session.actions.list_files import (
    ListFilesAction,
    ListFilesActionResult,
)
from ai.backend.manager.services.session.actions.match_sessions import (
    MatchSessionsAction,
    MatchSessionsActionResult,
)
from ai.backend.manager.services.session.actions.modify_session import (
    ModifySessionAction,
    ModifySessionActionResult,
)
from ai.backend.manager.services.session.actions.rename_session import (
    RenameSessionAction,
    RenameSessionActionResult,
)
from ai.backend.manager.services.session.actions.restart_session import (
    RestartSessionAction,
    RestartSessionActionResult,
)
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
    ShutdownServiceActionResult,
)
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
    StartServiceActionResult,
)
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
    UploadFilesActionResult,
)
from ai.backend.manager.types import UserScope
from ai.backend.manager.utils import query_userinfo

from ...data.image.types import ImageStatus

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


@dataclass
class SessionServiceArgs:
    db: ExtendedAsyncSAEngine
    agent_registry: AgentRegistry
    background_task_manager: BackgroundTaskManager
    event_hub: EventHub
    error_monitor: ErrorPluginContext
    idle_checker_host: IdleCheckerHost


class SessionService:
    _db: ExtendedAsyncSAEngine
    _agent_registry: AgentRegistry
    _background_task_manager: BackgroundTaskManager
    _event_hub: EventHub
    _error_monitor: ErrorPluginContext
    _idle_checker_host: IdleCheckerHost
    _database_ptask_group: aiotools.PersistentTaskGroup
    _rpc_ptask_group: aiotools.PersistentTaskGroup

    def __init__(
        self,
        args: SessionServiceArgs,
    ) -> None:
        self._db = args.db
        self._agent_registry = args.agent_registry
        self._event_hub = args.event_hub
        self._background_task_manager = args.background_task_manager
        self._error_monitor = args.error_monitor
        self._idle_checker_host = args.idle_checker_host
        self._database_ptask_group = aiotools.PersistentTaskGroup()
        self._rpc_ptask_group = aiotools.PersistentTaskGroup()
        self._webhook_ptask_group = aiotools.PersistentTaskGroup()

    async def commit_session(self, action: CommitSessionAction) -> CommitSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        filename = action.filename

        myself = asyncio.current_task()
        assert myself is not None

        try:
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )

            resp: Mapping[str, Any] = await asyncio.shield(
                self._rpc_ptask_group.create_task(
                    self._agent_registry.commit_session_to_file(session, filename),
                ),
            )
        except BackendAIError:
            log.exception("COMMIT_SESSION: exception")
            raise

        return CommitSessionActionResult(
            session_row=session,
            commit_result=resp,
        )

    async def complete(self, action: CompleteAction) -> CompleteActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        code = action.code
        options = action.options or {}

        resp = {
            "result": {
                "status": "finished",
                "completions": [],
            },
        }
        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        try:
            await self._agent_registry.increment_session_usage(session)
            resp["result"] = cast(
                Dict[str, Any],
                await self._agent_registry.get_completions(session, code, opts=options),
            )
        except AssertionError:
            raise InvalidAPIParameters
        except BackendAIError:
            log.exception("COMPLETE: exception")
            raise
        return CompleteActionResult(
            session_row=session,
            result=resp,
        )

    async def convert_session_to_image(
        self, action: ConvertSessionToImageAction
    ) -> ConvertSessionToImageActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        image_name = action.image_name
        image_visibility = action.image_visibility
        image_owner_id = action.image_owner_id

        myself = asyncio.current_task()
        assert myself is not None

        if image_visibility != CustomizedImageVisibilityScope.USER:
            raise InvalidAPIParameters(f"Unsupported visibility scope {image_visibility}")

        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                eager_loading_op=[selectinload(SessionRow.group)],
            )

        project: GroupRow = session.group
        if not project.container_registry:
            raise InvalidAPIParameters(
                "Project not ready to convert session image (registry configuration not populated)"
            )

        registry_hostname = project.container_registry["registry"]
        registry_project = project.container_registry["project"]

        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(ContainerRegistryRow)
                .where(
                    (ContainerRegistryRow.registry_name == registry_hostname)
                    & (ContainerRegistryRow.project == registry_project)
                )
                .options(
                    load_only(
                        ContainerRegistryRow.url,
                        ContainerRegistryRow.username,
                        ContainerRegistryRow.password,
                        ContainerRegistryRow.project,
                    )
                )
            )

            registry_conf = cast(ContainerRegistryRow | None, await db_session.scalar(query))

            if not registry_conf:
                raise InvalidAPIParameters(
                    f"Project {registry_project} not found in registry {registry_hostname}."
                )

        async with self._db.begin_readonly_session() as db_sess:
            image_row = await ImageRow.resolve(
                db_sess,
                [ImageIdentifier(session.main_kernel.image, session.main_kernel.architecture)],
            )

        base_image_ref = image_row.image_ref

        async def _commit_and_upload(reporter: ProgressReporter) -> None:
            reporter.total_progress = 3
            await reporter.update(message="Commit started")
            try:
                # remove any existing customized related tag from base canonical
                filtered_tag_set = [
                    x for x in base_image_ref.tag.split("-") if not x.startswith("customized_")
                ]

                if base_image_ref.name == "":
                    new_name = base_image_ref.project
                else:
                    new_name = base_image_ref.name

                new_canonical = f"{registry_hostname}/{registry_project}/{new_name}:{'-'.join(filtered_tag_set)}"

                async with self._db.begin_readonly_session() as sess:
                    # check if user has passed its limit of customized image count
                    query = (
                        sa.select([sa.func.count()])
                        .select_from(ImageRow)
                        .where(
                            (
                                ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                                == f"{image_visibility.value}:{image_owner_id}"
                            )
                        )
                        .where(ImageRow.status == ImageStatus.ALIVE)
                    )
                    existing_image_count = await sess.scalar(query)

                    customized_image_count_limit = action.max_customized_image_count
                    if customized_image_count_limit <= existing_image_count:
                        raise QuotaExceeded(
                            extra_msg="You have reached your customized image count quota",
                            extra_data={
                                "limit": customized_image_count_limit,
                                "current": existing_image_count,
                            },
                        )

                    # check if image with same name exists and reuse ID it if is
                    query = sa.select(ImageRow).where(
                        sa.and_(
                            ImageRow.name.like(f"{new_canonical}%"),
                            ImageRow.labels["ai.backend.customized-image.owner"].as_string()
                            == f"{image_visibility.value}:{image_owner_id}",
                            ImageRow.labels["ai.backend.customized-image.name"].as_string()
                            == image_name,
                            ImageRow.status == ImageStatus.ALIVE,
                        )
                    )
                    existing_row = await sess.scalar(query)

                    customized_image_id: str
                    kern_features: list[str]
                    if existing_row:
                        kern_features = existing_row.labels.get(
                            LabelName.FEATURES, DEFAULT_KERNEL_FEATURE
                        ).split()
                        customized_image_id = existing_row.labels[LabelName.CUSTOMIZED_ID]
                        log.debug("reusing existing customized image ID {}", customized_image_id)
                    else:
                        kern_features = [DEFAULT_KERNEL_FEATURE]
                        customized_image_id = str(uuid.uuid4())
                    # Remove PRIVATE label for customized images
                    kern_features = [
                        feat for feat in kern_features if feat != KernelFeatures.PRIVATE.value
                    ]

                new_canonical += f"-customized_{customized_image_id.replace('-', '')}"
                new_image_ref = ImageRef.from_image_str(
                    new_canonical,
                    None,
                    registry_hostname,
                    architecture=base_image_ref.architecture,
                    is_local=base_image_ref.is_local,
                )

                image_labels: dict[str | LabelName, str] = {
                    LabelName.CUSTOMIZED_OWNER: f"{image_visibility.value}:{image_owner_id}",
                    LabelName.CUSTOMIZED_NAME: image_name,
                    LabelName.CUSTOMIZED_ID: customized_image_id,
                    LabelName.FEATURES: " ".join(kern_features),
                }
                match image_visibility:
                    case CustomizedImageVisibilityScope.USER:
                        image_labels[LabelName.CUSTOMIZED_USER_EMAIL] = action.user_email

                # commit image with new tag set
                resp = await self._agent_registry.commit_session(
                    session,
                    new_image_ref,
                    extra_labels=image_labels,
                )
                bgtask_id = cast(uuid.UUID, resp["bgtask_id"])
                propagator = BgtaskPropagator(self._background_task_manager)
                self._event_hub.register_event_propagator(
                    propagator, [(EventDomain.BGTASK, str(bgtask_id))]
                )
                try:
                    async for event in propagator.receive(bgtask_id):
                        if not isinstance(event, BaseBgtaskDoneEvent):
                            log.warning("unexpected event: {}", event)
                            continue
                        match event.status():
                            case BgtaskStatus.DONE | BgtaskStatus.PARTIAL_SUCCESS:
                                # TODO: PARTIAL_SUCCESS should be handled
                                await reporter.update(increment=1, message="Committed image")
                                break
                            case BgtaskStatus.FAILED:
                                raise BgtaskFailedError(extra_msg=event.message)
                            case BgtaskStatus.CANCELLED:
                                raise BgtaskCancelledError(extra_msg="Operation cancelled")
                            case _:
                                log.warning("unexpected bgtask done event: {}", event)
                finally:
                    self._event_hub.unregister_event_propagator(propagator.id())

                if not new_image_ref.is_local:
                    # push image to registry from local agent
                    image_registry = ImageRegistry(
                        name=registry_hostname,
                        url=str(registry_conf.url),
                        username=registry_conf.username,
                        password=registry_conf.password,
                    )
                    resp = await self._agent_registry.push_image(
                        session.main_kernel.agent,
                        new_image_ref,
                        image_registry,
                    )
                    bgtask_id = cast(uuid.UUID, resp["bgtask_id"])
                    propagator = BgtaskPropagator(self._background_task_manager)
                    self._event_hub.register_event_propagator(
                        propagator, [(EventDomain.BGTASK, str(bgtask_id))]
                    )
                    try:
                        async for event in propagator.receive(bgtask_id):
                            if not isinstance(event, BaseBgtaskDoneEvent):
                                log.warning("unexpected event: {}", event)
                                continue
                            match event.status():
                                case BgtaskStatus.DONE | BgtaskStatus.PARTIAL_SUCCESS:
                                    break
                                case BgtaskStatus.FAILED:
                                    raise BgtaskFailedError(extra_msg=event.message)
                                case BgtaskStatus.CANCELLED:
                                    raise BgtaskCancelledError(extra_msg="Operation cancelled")
                                case _:
                                    log.warning("unexpected bgtask done event: {}", event)
                    finally:
                        self._event_hub.unregister_event_propagator(propagator.id())

                await reporter.update(increment=1, message="Pushed image to registry")
                # rescan updated image only
                await rescan_images(
                    self._db,
                    new_image_ref.canonical,
                    registry_project,
                    reporter=reporter,
                )
                await reporter.update(increment=1, message="Completed")
            except BackendAIError:
                log.exception("CONVERT_SESSION_TO_IMAGE: exception")
                raise

        task_id = await self._background_task_manager.start(_commit_and_upload)

        return ConvertSessionToImageActionResult(task_id=task_id, session_row=session)

    async def create_cluster(self, action: CreateClusterAction) -> CreateClusterActionResult:
        template_id = action.template_id
        user_id = action.user_id
        user_role = action.user_role
        sudo_session_enabled = action.sudo_session_enabled
        keypair_resource_policy = action.keypair_resource_policy
        requester_access_key = action.requester_access_key
        owner_access_key = action.owner_access_key
        domain_name = action.domain_name
        group_name = action.group_name
        scaling_group_name = action.scaling_group_name
        session_name = action.session_name
        session_type = action.session_type
        enqueue_only = action.enqueue_only
        max_wait_seconds = action.max_wait_seconds
        tag = action.tag

        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([session_templates.c.template])
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id) & session_templates.c.is_active,
                )
            )
            template = await conn.scalar(query)
            log.debug("task template: {}", template)
            if not template:
                raise TaskTemplateNotFound

            try:
                _owner_uuid, group_id, resource_policy = await query_userinfo(
                    conn,
                    user_id,
                    requester_access_key,
                    user_role,
                    domain_name,
                    keypair_resource_policy,
                    domain_name,
                    group_name,
                    query_on_behalf_of=(
                        None if owner_access_key is undefined else owner_access_key
                    ),
                )

            except ValueError as e:
                raise InvalidAPIParameters(str(e))

        try:
            resp = await self._agent_registry.create_cluster(
                template,
                session_name,
                UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_id,
                    user_role=user_role,
                ),
                owner_access_key,
                resource_policy,
                scaling_group_name,
                session_type,
                tag,
                enqueue_only=enqueue_only,
                max_wait_seconds=max_wait_seconds,
                sudo_session_enabled=sudo_session_enabled,
            )
            return CreateClusterActionResult(result=resp, session_id=resp["kernelId"])
        except TooManySessionsMatched:
            raise SessionAlreadyExists
        except BackendAIError:
            log.exception("GET_OR_CREATE: exception")
            raise
        except UnknownImageReference:
            raise UnknownImageReferenceError("Unknown image reference!")
        except Exception:
            await self._error_monitor.capture_exception()
            log.exception("GET_OR_CREATE: unexpected error!")
            raise InternalServerError

    async def create_from_params(
        self, action: CreateFromParamsAction
    ) -> CreateFromParamsActionResult:
        user_id = action.user_id
        user_role = action.user_role
        sudo_session_enabled = action.sudo_session_enabled
        keypair_resource_policy = action.keypair_resource_policy
        requester_access_key = action.requester_access_key

        owner_access_key = action.params.owner_access_key
        domain_name = action.params.domain_name
        group_name = action.params.group_name
        config = action.params.config
        cluster_size = action.params.cluster_size
        cluster_mode = action.params.cluster_mode
        session_name = action.params.session_name
        session_type = action.params.session_type
        enqueue_only = action.params.enqueue_only
        max_wait_seconds = action.params.max_wait_seconds
        tag = action.params.tag
        image = action.params.image
        architecture = action.params.architecture
        priority = action.params.priority
        bootstrap_script = action.params.bootstrap_script
        dependencies = action.params.dependencies
        startup_command = action.params.startup_command
        starts_at = action.params.starts_at
        batch_timeout = action.params.batch_timeout
        callback_url = action.params.callback_url
        reuse_if_exists = action.params.reuse_if_exists

        async with self._db.begin_readonly() as conn:
            owner_uuid, group_id, resource_policy = await query_userinfo(
                conn,
                user_id,
                requester_access_key,
                user_role,
                domain_name,
                keypair_resource_policy,
                domain_name,
                group_name,
                query_on_behalf_of=(None if owner_access_key is undefined else owner_access_key),
            )

        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        ImageIdentifier(
                            image,
                            architecture,
                        ),
                        ImageAlias(image),
                    ],
                )

            resp = await self._agent_registry.create_session(
                session_name,
                image_row.image_ref,
                UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_id,
                    user_role=user_role,
                ),
                owner_access_key,
                resource_policy,
                session_type,
                config,
                cluster_mode,
                cluster_size,
                reuse=reuse_if_exists,
                priority=priority,
                enqueue_only=enqueue_only,
                max_wait_seconds=max_wait_seconds,
                bootstrap_script=bootstrap_script,
                dependencies=dependencies,
                startup_command=startup_command,
                starts_at_timestamp=starts_at,
                batch_timeout=batch_timeout,
                tag=tag,
                callback_url=callback_url,
                sudo_session_enabled=sudo_session_enabled,
            )
            return CreateFromParamsActionResult(session_id=resp["sessionId"], result=resp)
        except UnknownImageReference:
            raise UnknownImageReferenceError(f"Unknown image reference: {image}")
        except BackendAIError:
            log.exception("GET_OR_CREATE: exception")
            raise
        except Exception:
            await self._error_monitor.capture_exception(context={"user": owner_uuid})
            log.exception("GET_OR_CREATE: unexpected error!")
            raise InternalServerError

    async def create_from_template(
        self, action: CreateFromTemplateAction
    ) -> CreateFromTemplateActionResult:
        template_id = action.params.template_id
        user_id = action.user_id
        user_role = action.user_role
        sudo_session_enabled = action.sudo_session_enabled
        keypair_resource_policy = action.keypair_resource_policy
        requester_access_key = action.requester_access_key

        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([session_templates])
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id) & session_templates.c.is_active,
                )
            )
            result = await conn.execute(query)
            template_info = result.fetchone()
            template = template_info["template"]
            if not template:
                raise TaskTemplateNotFound

            group_name = None
            if template_info["domain_name"] and template_info["group_id"]:
                query = (
                    sa.select([groups.c.name])
                    .select_from(groups)
                    .where(
                        (groups.c.domain_name == template_info["domain_name"])
                        & (groups.c.id == template_info["group_id"]),
                    )
                )
                group_name = await conn.scalar(query)

        if isinstance(template, str):
            template = load_json(template)

        log.debug("Template: {0}", template)

        param_from_template = {
            "image": template["spec"]["kernel"]["image"],
            "architecture": template["spec"]["kernel"]["architecture"],
        }

        if "domain_name" in template_info:
            param_from_template["domain"] = template_info["domain_name"]
        if group_name:
            param_from_template["group"] = group_name
        if template["spec"]["session_type"] == "interactive":
            param_from_template["session_type"] = SessionTypes.INTERACTIVE
        elif template["spec"]["session_type"] == "batch":
            param_from_template["session_type"] = SessionTypes.BATCH
        elif template["spec"]["session_type"] == "inference":
            param_from_template["session_type"] = SessionTypes.INFERENCE

        if tag := template["metadata"].get("tag"):
            param_from_template["tag"] = tag
        if runtime_opt := template["spec"]["kernel"]["run"]:
            if bootstrap := runtime_opt["bootstrap"]:
                param_from_template["bootstrap_script"] = bootstrap
            if startup := runtime_opt["startup_command"]:
                param_from_template["startup_command"] = startup

        config_from_template: MutableMapping[Any, Any] = {}
        if scaling_group := template["spec"].get("scaling_group"):
            config_from_template["scaling_group"] = scaling_group
        if mounts := template["spec"].get("mounts"):
            config_from_template["mounts"] = list(mounts.keys())
            config_from_template["mount_map"] = {
                key: value for (key, value) in mounts.items() if len(value) > 0
            }
        if environ := template["spec"]["kernel"].get("environ"):
            config_from_template["environ"] = environ
        if resources := template["spec"].get("resources"):
            config_from_template["resources"] = resources
        if "agent_list" in template["spec"]:
            config_from_template["agent_list"] = template["spec"]["agent_list"]

        override_config = drop_undefined(dict(action.params.config))
        override_params = drop_undefined(dict(asdict(action.params)))

        log.debug("Default config: {0}", config_from_template)
        log.debug("Default params: {0}", param_from_template)

        log.debug("Override config: {0}", override_config)
        log.debug("Override params: {0}", override_params)

        if override_config:
            config_from_template.update(override_config)
        if override_params:
            param_from_template.update(override_params)

        try:
            params = overwritten_param_check.check(param_from_template)
        except RuntimeError as e1:
            log.exception(e1)
        except t.DataError as e2:
            log.debug("Error: {0}", str(e2))
            raise InvalidAPIParameters("Error while validating template")
        params["config"] = config_from_template

        log.debug("Updated param: {0}", params)

        if git := template["spec"]["kernel"]["git"]:
            if _dest := git.get("dest_dir"):
                target = _dest
            else:
                target = git["repository"].split("/")[-1]

            cmd_builder = "git clone "
            if credential := git.get("credential"):
                proto, url = git["repository"].split("://")
                cmd_builder += f"{proto}://{credential['username']}:{credential['password']}@{url}"
            else:
                cmd_builder += git["repository"]
            if branch := git.get("branch"):
                cmd_builder += f" -b {branch}"
            cmd_builder += f" {target}\n"

            if commit := git.get("commit"):
                cmd_builder = "CWD=$(pwd)\n" + cmd_builder
                cmd_builder += f"cd {target}\n"
                cmd_builder += f"git checkout {commit}\n"
                cmd_builder += "cd $CWD\n"

            bootstrap = base64.b64decode(params.get("bootstrap_script") or b"").decode()
            bootstrap += "\n"
            bootstrap += cmd_builder
            params["bootstrap_script"] = base64.b64encode(bootstrap.encode()).decode()

        owner_access_key = params["owner_access_key"]
        config = params["config"]
        cluster_size = params["cluster_size"]
        cluster_mode = params["cluster_mode"]
        session_name = params["session_name"]
        session_type = params["session_type"]
        enqueue_only = params["enqueue_only"]
        max_wait_seconds = params["max_wait_seconds"]
        tag = params["tag"]
        image = params["image"]
        architecture = params["architecture"]
        priority = params["priority"]
        bootstrap_script = params["bootstrap_script"]
        dependencies = params["dependencies"]
        startup_command = params["startup_command"]
        starts_at = params["starts_at"]
        batch_timeout = params["batch_timeout"]
        callback_url = params["callback_url"]
        reuse_if_exists = params["reuse_if_exists"]
        domain_name = params["domain_name"]

        async with self._db.begin_readonly() as conn:
            owner_uuid, group_id, resource_policy = await query_userinfo(
                conn,
                user_id,
                requester_access_key,
                user_role,
                domain_name,
                keypair_resource_policy,
                domain_name,
                params["group_name"],
                query_on_behalf_of=(None if owner_access_key is undefined else owner_access_key),
            )

        try:
            async with self._db.begin_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        ImageIdentifier(
                            image,
                            architecture,
                        ),
                        ImageAlias(image),
                    ],
                )

            resp = await self._agent_registry.create_session(
                session_name,
                image_row.image_ref,
                UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_id,
                    user_role=user_role,
                ),
                owner_access_key,
                resource_policy,
                session_type,
                config,
                cluster_mode,
                cluster_size,
                reuse=reuse_if_exists,
                priority=priority,
                enqueue_only=enqueue_only,
                max_wait_seconds=max_wait_seconds,
                bootstrap_script=bootstrap_script,
                dependencies=dependencies,
                startup_command=startup_command,
                starts_at_timestamp=starts_at,
                batch_timeout=batch_timeout,
                tag=tag,
                callback_url=callback_url,
                sudo_session_enabled=sudo_session_enabled,
            )
            return CreateFromTemplateActionResult(session_id=resp["sessionId"], result=resp)
        except UnknownImageReference:
            raise UnknownImageReferenceError(f"Unknown image reference: {image}")
        except BackendAIError:
            log.exception("GET_OR_CREATE: exception")
            raise
        except Exception:
            await self._error_monitor.capture_exception(context={"user": owner_uuid})
            log.exception("GET_OR_CREATE: unexpected error!")
            raise InternalServerError

    async def destroy_session(self, action: DestroySessionAction) -> DestroySessionActionResult:
        user_role = action.user_role
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        forced = action.forced
        recursive = action.recursive

        if recursive:
            async with self._db.begin_readonly_session() as db_sess:
                dependent_session_ids = await find_dependent_sessions(
                    session_name,
                    db_sess,
                    owner_access_key,
                    allow_stale=True,
                )

                target_session_references: list[str | uuid.UUID] = [
                    *dependent_session_ids,
                    session_name,
                ]
                sessions: Iterable[SessionRow | BaseException] = await asyncio.gather(
                    *[
                        SessionRow.get_session(
                            db_sess,
                            name_or_id,
                            owner_access_key,
                            kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                        )
                        for name_or_id in target_session_references
                    ],
                    return_exceptions=True,
                )

            last_stats = await asyncio.gather(
                *[
                    self._agent_registry.destroy_session(sess, forced=forced, user_role=user_role)
                    for sess in sessions
                    if isinstance(sess, SessionRow)
                ],
                return_exceptions=True,
            )

            # Consider not found sessions already terminated.
            # Consider GenericForbidden error occurs with scheduled/preparing/terminating/error status session, and leave them not to be quitted.
            last_stats = [
                *filter(lambda x: not isinstance(x, SessionNotFound | GenericForbidden), last_stats)
            ]

            return DestroySessionActionResult(result=last_stats, destroyed_sessions=sessions)
        else:
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
                )
            last_stat = await self._agent_registry.destroy_session(
                session,
                forced=forced,
                user_role=user_role,
            )
            resp = {
                "stats": last_stat,
            }

            return DestroySessionActionResult(result=resp, destroyed_sessions=[session])

    async def download_file(self, action: DownloadFileAction) -> DownloadFileActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        user_id = action.user_id
        file = action.file

        try:
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )
            await self._agent_registry.increment_session_usage(session)
            result = await self._agent_registry.download_single(session, owner_access_key, file)
        except asyncio.CancelledError:
            raise
        except BackendAIError:
            log.exception("DOWNLOAD_SINGLE: exception")
            raise
        except (ValueError, FileNotFoundError):
            raise InvalidAPIParameters("The file is not found.")
        except Exception:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("DOWNLOAD_SINGLE: unexpected error!")
            raise InternalServerError

        return DownloadFileActionResult(result=result, session_row=session)

    async def download_files(self, action: DownloadFilesAction) -> DownloadFilesActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        user_id = action.user_id
        files = action.files

        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        try:
            assert len(files) <= 5, "Too many files"
            await self._agent_registry.increment_session_usage(session)
            # TODO: Read all download file contents. Need to fix by using chuncking, etc.
            results = await asyncio.gather(
                *map(
                    functools.partial(self._agent_registry.download_file, session),
                    files,
                ),
            )
            log.debug("file(s) inside container retrieved")
        except asyncio.CancelledError:
            raise
        except BackendAIError:
            log.exception("DOWNLOAD_FILE: exception")
            raise
        except (ValueError, FileNotFoundError):
            raise InvalidAPIParameters("The file is not found.")
        except Exception:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("DOWNLOAD_FILE: unexpected error!")
            raise InternalServerError

        with aiohttp.MultipartWriter("mixed") as mpwriter:
            headers = multidict.MultiDict({"Content-Encoding": "identity"})
            for tarbytes in results:
                mpwriter.append(tarbytes, headers)

            return DownloadFilesActionResult(
                session_row=session,
                result=mpwriter,  # type: ignore
            )

    async def execute_session(self, action: ExecuteSessionAction) -> ExecuteSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        api_version = action.api_version

        resp = {}
        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        try:
            await self._agent_registry.increment_session_usage(session)

            run_id: Optional[str]
            mode: Optional[str]

            if api_version[0] == 1:
                run_id = action.params.run_id or secrets.token_hex(8)
                mode = "query"
                code = action.params.code
                opts = None
            elif api_version[0] >= 2:
                run_id = action.params.run_id
                mode = action.params.mode

                if mode is None:
                    # TODO: Create new exception
                    raise RuntimeError("runId or mode is missing!")

                assert mode in {
                    "query",
                    "batch",
                    "complete",
                    "continue",
                    "input",
                }, "mode has an invalid value."
                if mode in {"continue", "input"}:
                    assert run_id is not None, "continuation requires explicit run ID"
                code = action.params.code
                opts = action.params.options
            else:
                raise RuntimeError("should not reach here")
            # handle cases when some params are deliberately set to None
            if code is None:
                code = ""  # noqa
            if opts is None:
                opts = {}  # noqa
            if mode == "complete":
                # For legacy
                resp["result"] = await self._agent_registry.get_completions(session, code, opts)
            else:
                run_id = cast(str, run_id)
                raw_result = await self._agent_registry.execute(
                    session,
                    api_version,
                    run_id,
                    mode,
                    code,
                    opts,
                    flush_timeout=2.0,
                )
                if raw_result is None:
                    # the kernel may have terminated from its side,
                    # or there was interruption of agents.
                    resp["result"] = {
                        "status": "finished",
                        "runId": run_id,
                        "exitCode": 130,
                        "options": {},
                        "files": [],
                        "console": [],
                    }
                    return ExecuteSessionActionResult(result=resp, session_row=session)
                # Keep internal/public API compatilibty
                result = {
                    "status": raw_result["status"],
                    "runId": raw_result["runId"],
                    "exitCode": raw_result.get("exitCode"),
                    "options": raw_result.get("options"),
                    "files": raw_result.get("files"),
                }
                if api_version[0] == 1:
                    result["stdout"] = raw_result.get("stdout")
                    result["stderr"] = raw_result.get("stderr")
                    result["media"] = raw_result.get("media")
                    result["html"] = raw_result.get("html")
                else:
                    result["console"] = raw_result.get("console")
                resp["result"] = result
        except AssertionError as e:
            log.warning("EXECUTE: invalid/missing parameters: {0!r}", e)
            raise InvalidAPIParameters(extra_msg=e.args[0])
        except BackendAIError:
            log.exception("EXECUTE: exception")
            raise

        return ExecuteSessionActionResult(result=resp, session_row=session)

    async def get_abusing_report(
        self, action: GetAbusingReportAction
    ) -> GetAbusingReportActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        try:
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )
            kernel = session.main_kernel
            report = await self._agent_registry.get_abusing_report(kernel.id)
        except BackendAIError:
            log.exception("GET_ABUSING_REPORT: exception")
            raise
        return GetAbusingReportActionResult(result=report, session_row=session)

    async def get_commit_status(self, action: GetCommitStatusAction) -> GetCommitStatusActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        try:
            async with self._db.begin_readonly_session() as db_sess:
                session = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )
            statuses = await self._agent_registry.get_commit_status([session.main_kernel.id])
        except BackendAIError:
            log.exception("GET_COMMIT_STATUS: exception")
            raise
        resp = {"status": statuses[session.main_kernel.id], "kernel": str(session.main_kernel.id)}
        return GetCommitStatusActionResult(result=resp, session_row=session)

    async def get_container_logs(
        self, action: GetContainerLogsAction
    ) -> GetContainerLogsActionResult:
        resp = {"result": {"logs": ""}}
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        kernel_id = action.kernel_id

        async with self._db.begin_readonly_session() as db_sess:
            compute_session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                allow_stale=True,
                kernel_loading_strategy=(
                    KernelLoadingStrategy.MAIN_KERNEL_ONLY
                    if kernel_id is None
                    else KernelLoadingStrategy.ALL_KERNELS
                ),
            )

            if compute_session.status in DEAD_SESSION_STATUSES:
                if kernel_id is None:
                    # Get logs from the main kernel
                    kernel_id = compute_session.main_kernel.id
                    kernel_log = compute_session.main_kernel.container_log
                else:
                    # Get logs from the specific kernel
                    kernel_row = compute_session.get_kernel_by_id(kernel_id)
                    kernel_log = kernel_row.container_log
                if kernel_log is not None:
                    # Get logs from database record
                    log.debug("returning log from database record")
                    resp["result"]["logs"] = kernel_log.decode("utf-8")
                    return GetContainerLogsActionResult(result=resp, session_row=compute_session)

        registry = self._agent_registry
        await registry.increment_session_usage(compute_session)
        resp["result"]["logs"] = await registry.get_logs_from_agent(
            session=compute_session, kernel_id=kernel_id
        )
        log.debug("returning log from agent")

        return GetContainerLogsActionResult(result=resp, session_row=compute_session)

    async def get_dependency_graph(
        self, action: GetDependencyGraphAction
    ) -> GetDependencyGraphActionResult:
        root_session_name = action.root_session_name
        owner_access_key = action.owner_access_key

        async with self._db.begin_readonly_session() as db_session:
            # TODO: Move `find_dependency_sessions` impl to Service layer
            dependency_graph = await find_dependency_sessions(
                root_session_name, db_session, owner_access_key
            )
            session_id = dependency_graph["session_id"]
            stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
            session = await db_session.scalar(stmt)

        return GetDependencyGraphActionResult(result=dependency_graph, session_row=session)

    async def get_direct_access_info(
        self, action: GetDirectAccessInfoAction
    ) -> GetDirectAccessInfoActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        async with self._db.begin_session() as db_sess:
            sess = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        resp = {}
        sess_type = cast(SessionTypes, sess.session_type)
        if sess_type in PRIVATE_SESSION_TYPES:
            public_host = sess.main_kernel.agent_row.public_host
            found_ports: dict[str, list[str]] = {}
            for sport in sess.main_kernel.service_ports:
                if sport["name"] == "sshd":
                    found_ports["sshd"] = sport["host_ports"]
                elif sport["name"] == "sftpd":
                    found_ports["sftpd"] = sport["host_ports"]
            resp = {
                "kernel_role": sess_type.name,  # legacy
                "session_type": sess_type.name,
                "public_host": public_host,
                "sshd_ports": found_ports.get("sftpd") or found_ports["sshd"],
            }

        return GetDirectAccessInfoActionResult(result=resp, session_row=sess)

    async def get_session_info(self, action: GetSessionInfoAction) -> GetSessionInfoActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        resp = {}
        async with self._db.begin_session() as db_sess:
            sess = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        await self._agent_registry.increment_session_usage(sess)
        resp["domainName"] = sess.domain_name
        resp["groupId"] = str(sess.group_id)
        resp["userId"] = str(sess.user_uuid)
        resp["lang"] = sess.main_kernel.image  # legacy
        resp["image"] = sess.main_kernel.image
        resp["architecture"] = sess.main_kernel.architecture
        resp["registry"] = sess.main_kernel.registry
        resp["tag"] = sess.tag

        # Resource occupation
        resp["containerId"] = str(sess.main_kernel.container_id)
        resp["occupiedSlots"] = str(sess.main_kernel.occupied_slots)  # legacy
        resp["occupyingSlots"] = str(sess.occupying_slots)
        resp["requestedSlots"] = str(sess.requested_slots)
        resp["occupiedShares"] = str(
            sess.main_kernel.occupied_shares
        )  # legacy, only caculate main kernel's occupying resource
        resp["environ"] = str(sess.environ)
        resp["resourceOpts"] = str(sess.resource_opts)

        # Lifecycle
        resp["status"] = sess.status.name  # "e.g. 'SessionStatus.RUNNING' -> 'RUNNING' "
        resp["statusInfo"] = str(sess.status_info)
        resp["statusData"] = sess.status_data
        age = datetime.now(tzutc()) - sess.created_at
        resp["age"] = int(age.total_seconds() * 1000)  # age in milliseconds
        resp["creationTime"] = str(sess.created_at)
        resp["terminationTime"] = str(sess.terminated_at) if sess.terminated_at else None

        resp["numQueriesExecuted"] = sess.num_queries
        resp["lastStat"] = sess.last_stat
        resp["idleChecks"] = await self._idle_checker_host.get_idle_check_report(sess.id)

        # Resource limits collected from agent heartbeats were erased, as they were deprecated
        # TODO: factor out policy/image info as a common repository

        return GetSessionInfoActionResult(result=resp, session_row=sess)

    async def interrupt(self, action: InterruptSessionAction) -> InterruptSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        await self._agent_registry.increment_session_usage(session)
        await self._agent_registry.interrupt_session(session)

        return InterruptSessionActionResult(result=None, session_row=session)

    async def list_files(self, action: ListFilesAction) -> ListFilesActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        user_id = action.user_id
        path = action.path

        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )

        resp: MutableMapping[str, Any] = {}
        try:
            await self._agent_registry.increment_session_usage(session)
            result = await self._agent_registry.list_files(session, path)
            resp.update(result)
            log.debug("container file list for {0} retrieved", path)
        except asyncio.CancelledError:
            raise
        except BackendAIError:
            log.exception("LIST_FILES: exception")
            raise
        except Exception:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("LIST_FILES: unexpected error!")
            raise InternalServerError

        return ListFilesActionResult(result=result, session_row=session)

    async def match_sessions(self, action: MatchSessionsAction) -> MatchSessionsActionResult:
        id_or_name_prefix = action.id_or_name_prefix
        owner_access_key = action.owner_access_key

        matches: list[dict[str, Any]] = []
        async with self._db.begin_readonly_session() as db_sess:
            sessions = await SessionRow.match_sessions(
                db_sess,
                id_or_name_prefix,
                owner_access_key,
            )
        if sessions:
            matches.extend(
                {
                    "id": str(item.id),
                    "name": item.name,
                    "status": item.status.name,
                }
                for item in sessions
            )
        return MatchSessionsActionResult(result=matches)

    async def rename_session(self, action: RenameSessionAction) -> RenameSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        new_name = action.new_name

        async with self._db.begin_session() as db_sess:
            compute_session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                allow_stale=True,
                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
            )
            if compute_session.status != SessionStatus.RUNNING:
                raise InvalidAPIParameters("Can't change name of not running session")
            compute_session.name = new_name
            for kernel in compute_session.kernels:
                kernel.session_name = new_name
            await db_sess.commit()

        return RenameSessionActionResult(result=None, session_row=compute_session)

    async def restart_session(self, action: RestartSessionAction) -> RestartSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        async with self._db.begin_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
            )
        await self._agent_registry.increment_session_usage(session)
        await self._agent_registry.restart_session(session)
        return RestartSessionActionResult(result=None, session_row=session)

    async def shutdown_service(self, action: ShutdownServiceAction) -> ShutdownServiceActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        service_name = action.service_name

        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
        await self._agent_registry.shutdown_service(session, service_name)
        return ShutdownServiceActionResult(result=None, session_row=session)

    async def start_service(self, action: StartServiceAction) -> StartServiceActionResult:
        session_name = action.session_name
        access_key = action.access_key
        service = action.service
        port = action.port

        arguments = action.arguments
        envs = action.envs
        login_session_token = action.login_session_token

        try:
            async with self._db.begin_readonly_session() as db_sess:
                session = await asyncio.shield(
                    self._database_ptask_group.create_task(
                        SessionRow.get_session(
                            db_sess,
                            session_name,
                            access_key,
                            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                            eager_loading_op=[
                                selectinload(SessionRow.routing).options(noload("*")),
                            ],
                        ),
                    )
                )
        except (SessionNotFound, TooManySessionsMatched):
            raise

        query = (
            sa.select([scaling_groups.c.wsproxy_addr])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == session.scaling_group_name))
        )

        async with self._db.begin_readonly() as conn:
            result = await conn.execute(query)
            sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        if not wsproxy_addr:
            raise ServiceUnavailable("No coordinator configured for this resource group")
        wsproxy_status = await query_wsproxy_status(wsproxy_addr)
        if advertise_addr := wsproxy_status.get("advertise_address"):
            wsproxy_advertise_addr = advertise_addr
        else:
            wsproxy_advertise_addr = wsproxy_addr

        if session.main_kernel.kernel_host is None:
            kernel_host = urlparse(session.main_kernel.agent_addr).hostname
        else:
            kernel_host = session.main_kernel.kernel_host
        for sport in session.main_kernel.service_ports:
            if sport["name"] == service:
                if sport["is_inference"]:
                    raise InvalidAPIParameters(
                        f"{service} is an inference app. Starting inference apps can only be done by"
                        " starting an inference service."
                    )
                if port:
                    # using one of the primary/secondary ports of the app
                    try:
                        hport_idx = sport["container_ports"].index(port)
                    except ValueError:
                        raise InvalidAPIParameters(
                            f"Service {service} does not open the port number {port}."
                        )
                    host_port = sport["host_ports"][hport_idx]
                else:
                    # using the default (primary) port of the app
                    if "host_ports" not in sport:
                        host_port = sport["host_port"]  # legacy kernels
                    else:
                        host_port = sport["host_ports"][0]
                break
        else:
            raise AppNotFound(f"{session_name}:{service}")

        await asyncio.shield(
            self._database_ptask_group.create_task(
                self._agent_registry.increment_session_usage(session),
            )
        )

        opts: MutableMapping[str, Union[None, str, list[str]]] = {}
        if arguments is not None:
            opts["arguments"] = load_json(arguments)
        if envs is not None:
            opts["envs"] = load_json(envs)

        result = await asyncio.shield(
            self._rpc_ptask_group.create_task(
                self._agent_registry.start_service(session, service, opts),
            ),
        )
        if result["status"] == "failed":
            raise InternalServerError(
                "Failed to launch the app service", extra_data=result["error"]
            )

        body = {
            "login_session_token": login_session_token,
            "kernel_host": kernel_host,
            "kernel_port": host_port,
            "session": {
                "id": str(session.id),
                "user_uuid": str(session.user_uuid),
                "group_id": str(session.group_id),
                "access_key": session.access_key,
                "domain_name": session.domain_name,
            },
        }

        async with aiohttp.ClientSession() as req:
            async with req.post(
                f"{wsproxy_addr}/v2/conf",
                json=body,
            ) as resp:
                token_json = await resp.json()

                return StartServiceActionResult(
                    result=None,
                    session_row=session,
                    token=token_json["token"],
                    wsproxy_addr=wsproxy_advertise_addr,
                )

    async def upload_files(self, action: UploadFilesAction) -> UploadFilesActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        reader = action.reader

        loop = asyncio.get_event_loop()

        async with self._db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )

        await self._agent_registry.increment_session_usage(session)
        file_count = 0
        upload_tasks = []
        async for file in aiotools.aiter(reader.next, None):
            if file_count == 20:
                raise InvalidAPIParameters("Too many files")
            file_count += 1
            # This API handles only small files, so let's read it at once.
            chunks = []
            recv_size = 0
            while True:
                chunk = await file.read_chunk(size=1048576)
                if not chunk:
                    break
                chunk_size = len(chunk)
                if recv_size + chunk_size >= 1048576:
                    raise InvalidAPIParameters("Too large file")
                chunks.append(chunk)
                recv_size += chunk_size
            data = file.decode(b"".join(chunks))
            log.debug("received file: {0} ({1:,} bytes)", file.filename, recv_size)
            t = loop.create_task(self._agent_registry.upload_file(session, file.filename, data))
            upload_tasks.append(t)
        await asyncio.gather(*upload_tasks)

        return UploadFilesActionResult(result=None, session_row=session)

    async def modify_session(self, action: ModifySessionAction) -> ModifySessionActionResult:
        session_id = action.session_id
        props = action.modifier
        session_name = action.modifier.name.optional_value()

        async def _update(db_session: AsyncSession) -> Optional[SessionRow]:
            query_stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
            session_row = await db_session.scalar(query_stmt)
            if session_row is None:
                raise ValueError(f"Session not found (id:{session_id})")
            session_row = cast(SessionRow, session_row)

            if session_name:
                # Check the owner of the target session has any session with the same name
                try:
                    sess = await SessionRow.get_session(
                        db_session,
                        session_name,
                        AccessKey(session_row.access_key),
                    )
                except SessionNotFound:
                    pass
                else:
                    raise ValueError(
                        f"Duplicate session name. Session(id:{sess.id}) already has the name"
                    )
            select_stmt = (
                sa.select(SessionRow)
                .options(selectinload(SessionRow.kernels))
                .execution_options(populate_existing=True)
                .where(SessionRow.id == session_id)
            )

            session_row = await db_session.scalar(select_stmt)
            to_update = props.fields_to_update()
            for key, value in to_update.items():
                setattr(session_row, key, value)

            if session_name:
                await db_session.execute(
                    sa.update(KernelRow)
                    .values(session_name=session_name)
                    .where(KernelRow.session_id == session_id)
                )
            return session_row

        async with self._db.connect() as db_conn:
            session_row = await execute_with_txn_retry(_update, self._db.begin_session, db_conn)
        if session_row is None:
            raise ValueError(f"Session not found (id:{session_id})")

        return ModifySessionActionResult(result=None, session_row=session_row)

    async def check_and_transit_status(
        self, action: CheckAndTransitStatusAction
    ) -> CheckAndTransitStatusActionResult:
        user_id = action.user_id
        user_role = action.user_role
        session_id = action.session_id

        async with self._db.begin_readonly_session() as db_session:
            session_row = await SessionRow.get_session_to_determine_status(db_session, session_id)
            if session_row.user_uuid != user_id and user_role not in (
                UserRole.ADMIN,
                UserRole.SUPERADMIN,
            ):
                log.warning(
                    f"You are not allowed to transit others's sessions status, skip (s:{session_id})"
                )
                return CheckAndTransitStatusActionResult(result={}, session_row=session_row)

        now = datetime.now(tzutc())
        session_rows = await self._agent_registry.session_lifecycle_mgr.transit_session_status(
            [session_id], now
        )
        await self._agent_registry.session_lifecycle_mgr.deregister_status_updatable_session([
            row.id for row, is_transited in session_rows if is_transited
        ])

        result = {row.id: row.status.name for row, _ in session_rows}
        return CheckAndTransitStatusActionResult(result=result, session_row=session_row)

    async def check_and_transit_status_multi(
        self, action: CheckAndTransitStatusBatchAction
    ) -> CheckAndTransitStatusBatchActionResult:
        user_id = action.user_id
        user_role = action.user_role
        session_ids = action.session_ids
        accessible_session_ids: list[SessionId] = []

        async with self._db.begin_readonly_session() as db_session:
            for sid in session_ids:
                session_row = await SessionRow.get_session_to_determine_status(db_session, sid)
                if session_row.user_uuid == user_id or user_role in (
                    UserRole.ADMIN,
                    UserRole.SUPERADMIN,
                ):
                    accessible_session_ids.append(sid)
                else:
                    log.warning(
                        f"You are not allowed to transit others's sessions status, skip (s:{sid})"
                    )

        now = datetime.now(tzutc())
        if accessible_session_ids:
            session_rows = await self._agent_registry.session_lifecycle_mgr.transit_session_status(
                accessible_session_ids, now
            )
            await self._agent_registry.session_lifecycle_mgr.deregister_status_updatable_session([
                row.id for row, is_transited in session_rows if is_transited
            ])
            result = {row.id: row.status.name for row, _ in session_rows}
        else:
            result = {}

        return CheckAndTransitStatusBatchActionResult(session_status_map=result)
