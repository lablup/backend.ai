import asyncio
import base64
import functools
import logging
import secrets
import uuid
from collections.abc import Mapping, MutableMapping
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, cast
from urllib.parse import urlparse

import aiohttp
import aiotools
import multidict
import trafaret as t
import yarl
from aiohttp.multipart import BodyPartReader
from dateutil.tz import tzutc

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.defs.session import SESSION_PRIORITY_DEFAULT
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.exception import (
    BackendAIError,
    InvalidAPIParameters,
    UnknownImageReference,
)
from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.json import load_json
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    BinarySize,
    ContainerId,
    ImageAlias,
    ResourceSlotEntry,
    SessionTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.utils import undefined
from ai.backend.manager.bgtask.tasks.commit_session import CommitSessionManifest
from ai.backend.manager.bgtask.types import ManagerBgtaskName
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.data.image.types import ImageIdentifier
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
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.common import (
    InternalServerError,
    ServiceUnavailable,
)
from ai.backend.manager.errors.image import UnknownImageReferenceError
from ai.backend.manager.errors.kernel import (
    InvalidSessionData,
    KernelNotReady,
    QuotaExceeded,
    SessionAlreadyExists,
    SessionNotFound,
    TooManySessionsMatched,
)
from ai.backend.manager.errors.resource import (
    AgentNotAllocated,
    AppNotFound,
    NoCurrentTaskContext,
    TaskTemplateNotFound,
)
from ai.backend.manager.errors.storage import VFolderBadRequest
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.session import (
    DEAD_SESSION_STATUSES,
    PRIVATE_SESSION_TYPES,
    KernelLoadingStrategy,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.session.updaters import SessionUpdaterSpec
from ai.backend.manager.repositories.user.repository import UserRepository
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
from ai.backend.manager.services.session.actions.destroy_session import (
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
from ai.backend.manager.services.session.actions.enqueue_session import (
    EnqueueSessionAction,
    EnqueueSessionActionResult,
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
from ai.backend.manager.services.session.actions.get_session import (
    GetSessionAction,
    GetSessionActionResult,
)
from ai.backend.manager.services.session.actions.get_session_info import (
    GetSessionInfoAction,
    GetSessionInfoActionResult,
)
from ai.backend.manager.services.session.actions.get_status_history import (
    GetStatusHistoryAction,
    GetStatusHistoryActionResult,
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
from ai.backend.manager.services.session.actions.resolve_session import (
    ResolveSessionAction,
    ResolveSessionActionResult,
)
from ai.backend.manager.services.session.actions.search import (
    SearchSessionsAction,
    SearchSessionsActionResult,
)
from ai.backend.manager.services.session.actions.search_in_project import (
    SearchSessionsInProjectAction,
    SearchSessionsInProjectActionResult,
)
from ai.backend.manager.services.session.actions.search_kernel import (
    SearchKernelsAction,
    SearchKernelsActionResult,
)
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
    ShutdownServiceActionResult,
)
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
    StartServiceActionResult,
)
from ai.backend.manager.services.session.actions.terminate_sessions import (
    TerminateSessionsAction,
    TerminateSessionsActionResult,
)
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
    UploadFilesActionResult,
)
from ai.backend.manager.services.session.types import (
    CommitStatusInfo,
    LegacySessionInfo,
    overwritten_param_check,
)
from ai.backend.manager.services.session.utils import drop_undefined
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import UserScope

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SessionServiceArgs:
    agent_registry: AgentRegistry
    event_fetcher: EventFetcher
    background_task_manager: BackgroundTaskManager
    event_hub: EventHub
    error_monitor: ErrorPluginContext
    idle_checker_host: IdleCheckerHost
    session_repository: SessionRepository
    scheduler_repository: SchedulerRepository
    scheduling_controller: SchedulingController
    appproxy_client_pool: AppProxyClientPool
    user_repository: UserRepository


class SessionService:
    _agent_registry: AgentRegistry
    _background_task_manager: BackgroundTaskManager
    _event_fetcher: EventFetcher
    _event_hub: EventHub
    _error_monitor: ErrorPluginContext
    _idle_checker_host: IdleCheckerHost
    _session_repository: SessionRepository
    _scheduler_repository: SchedulerRepository
    _user_repository: UserRepository
    _scheduling_controller: SchedulingController
    _appproxy_client_pool: AppProxyClientPool
    _database_ptask_group: aiotools.PersistentTaskGroup
    _rpc_ptask_group: aiotools.PersistentTaskGroup

    def __init__(
        self,
        args: SessionServiceArgs,
    ) -> None:
        self._agent_registry = args.agent_registry
        self._event_hub = args.event_hub
        self._event_fetcher = args.event_fetcher
        self._background_task_manager = args.background_task_manager
        self._error_monitor = args.error_monitor
        self._idle_checker_host = args.idle_checker_host
        self._session_repository = args.session_repository
        self._scheduler_repository = args.scheduler_repository
        self._user_repository = args.user_repository
        self._scheduling_controller = args.scheduling_controller
        self._appproxy_client_pool = args.appproxy_client_pool
        self._database_ptask_group = aiotools.PersistentTaskGroup()
        self._rpc_ptask_group = aiotools.PersistentTaskGroup()
        self._webhook_ptask_group = aiotools.PersistentTaskGroup()

    async def resolve_session(self, action: ResolveSessionAction) -> ResolveSessionActionResult:
        """Resolve a live session to its ``session_id`` by ``(session_name, user_id)``.
        DO NOT USE THIS FOR NEW DEVELOPMENT. This is only for backward compatibility with existing resolvers.

        Callers go through this resolver before invoking any other session operation, so
        that downstream lookups can rely solely on ``session_id``. The ``user_id`` scope
        covers sessions created with any of the user's keypair access keys.
        """
        session_id = await self._session_repository.resolve_session_id(
            action.session_name,
            action.user_id,
        )
        return ResolveSessionActionResult(session_id=session_id)

    async def commit_session(self, action: CommitSessionAction) -> CommitSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        filename = action.filename

        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current asyncio task context available")

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )

        resp: Mapping[str, Any] = await asyncio.shield(
            self._rpc_ptask_group.create_task(
                self._agent_registry.commit_session_to_file(session, filename),
            ),
        )

        return CommitSessionActionResult(
            session_data=session.to_dataclass(),
            commit_result=resp,
        )

    async def complete(self, action: CompleteAction) -> CompleteActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        code = action.code
        options = action.options or {}

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        try:
            resp = await self._agent_registry.get_completions(session, code, opts=options)
        except AssertionError as e:
            raise InvalidAPIParameters from e
        return CompleteActionResult(
            session_data=session.to_dataclass(),
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
        if myself is None:
            raise NoCurrentTaskContext("No current asyncio task context available")

        if image_visibility != CustomizedImageVisibilityScope.USER:
            raise InvalidAPIParameters(f"Unsupported visibility scope {image_visibility}")

        # check if user has passed its limit of customized image count
        existing_image_count = await self._session_repository.get_customized_image_count(
            image_visibility.value, str(image_owner_id)
        )
        customized_image_count_limit = action.max_customized_image_count
        if customized_image_count_limit <= existing_image_count:
            raise QuotaExceeded(
                extra_msg=(
                    "You have reached your customized image count quota. "
                    f"(current: {existing_image_count}, limit: {customized_image_count_limit})"
                ),
                extra_data={
                    "limit": customized_image_count_limit,
                    "current": existing_image_count,
                },
            )

        session = await self._session_repository.get_session_with_group(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )

        project: GroupRow = session.group
        if not project.container_registry:
            raise InvalidAPIParameters(
                "Project not ready to convert session image (registry configuration not populated)"
            )

        registry_hostname = project.container_registry["registry"]
        registry_project = project.container_registry["project"]

        registry_conf = await self._session_repository.get_container_registry(
            registry_hostname, registry_project
        )
        if not registry_conf:
            raise InvalidAPIParameters(
                f"Project {registry_project} not found in registry {registry_hostname}."
            )

        # Validate image exists
        if session.main_kernel.image and session.main_kernel.architecture:
            await self._session_repository.resolve_image(
                [ImageIdentifier(session.main_kernel.image, session.main_kernel.architecture)],
                alive_only=False,
            )

        # Create manifest for background task
        manifest = CommitSessionManifest(
            session_id=session.id,
            registry_hostname=registry_hostname,
            registry_project=registry_project,
            image_name=image_name,
            image_visibility=image_visibility,
            image_owner_id=str(image_owner_id),
            user_email=action.user_email,
        )

        task_id = await self._background_task_manager.start_retriable(
            ManagerBgtaskName.COMMIT_SESSION,
            manifest,
        )

        return ConvertSessionToImageActionResult(
            task_id=task_id, session_data=session.to_dataclass()
        )

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

        template = await self._session_repository.get_template_by_id(template_id)
        log.debug("task template: {}", template)
        if not template:
            raise TaskTemplateNotFound

        try:
            user_info = await self._session_repository.query_userinfo(
                user_id,
                requester_access_key,
                user_role,
                domain_name,
                keypair_resource_policy,
                domain_name,
                group_name,
                query_on_behalf_of=owner_access_key,
            )
        except ValueError as e:
            raise InvalidAPIParameters(str(e)) from e

        try:
            resp = await self._agent_registry.create_cluster(
                template,
                session_name,
                UserScope(
                    domain_name=domain_name,
                    group_id=user_info.group_id,
                    user_uuid=user_info.owner_uuid,
                    user_role=user_info.owner_role.value,
                ),
                owner_access_key,
                user_info.resource_policy,
                scaling_group_name,
                session_type,
                tag,
                enqueue_only=enqueue_only,
                max_wait_seconds=max_wait_seconds,
                sudo_session_enabled=sudo_session_enabled,
            )
            return CreateClusterActionResult(result=resp, session_id=resp["kernelId"])
        except TooManySessionsMatched as e:
            raise SessionAlreadyExists from e
        except BackendAIError:
            raise
        except UnknownImageReference as e:
            raise UnknownImageReferenceError("Unknown image reference!") from e
        except Exception as e:
            await self._error_monitor.capture_exception()
            log.exception("GET_OR_CREATE: unexpected error!", e)
            raise InternalServerError from e

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
        is_preemptible = action.params.is_preemptible
        bootstrap_script = action.params.bootstrap_script
        dependencies = action.params.dependencies
        startup_command = action.params.startup_command
        starts_at = action.params.starts_at
        batch_timeout = action.params.batch_timeout
        callback_url = action.params.callback_url
        reuse_if_exists = action.params.reuse_if_exists

        user_info = await self._session_repository.query_userinfo(
            user_id,
            requester_access_key,
            user_role,
            domain_name,
            keypair_resource_policy,
            domain_name,
            group_name,
            query_on_behalf_of=owner_access_key,
        )

        try:
            image_row = await self._session_repository.resolve_image([
                ImageIdentifier(
                    image,
                    architecture,
                ),
                ImageAlias(image),
            ])

            resp = await self._agent_registry.create_session(
                session_name,
                image_row.image_ref,
                UserScope(
                    domain_name=domain_name,
                    group_id=user_info.group_id,
                    user_uuid=user_info.owner_uuid,
                    user_role=user_info.owner_role.value,
                ),
                owner_access_key,
                user_info.resource_policy,
                session_type,
                config,
                cluster_mode,
                cluster_size,
                reuse=reuse_if_exists,
                priority=priority,
                is_preemptible=is_preemptible,
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
            await self._session_repository.update_image_last_used_at(
                image_row.id, datetime.now(tzutc())
            )
            return CreateFromParamsActionResult(
                session_id=uuid.UUID(resp["sessionId"]), result=resp
            )
        except UnknownImageReference as e:
            raise UnknownImageReferenceError(f"Unknown image reference: {image}") from e
        except BackendAIError:
            raise
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": user_info.owner_uuid})
            log.exception("GET_OR_CREATE: unexpected error!", e)
            raise InternalServerError from e

    async def create_from_template(
        self, action: CreateFromTemplateAction
    ) -> CreateFromTemplateActionResult:
        template_id = action.params.template_id
        user_id = action.user_id
        user_role = action.user_role
        sudo_session_enabled = action.sudo_session_enabled
        keypair_resource_policy = action.keypair_resource_policy
        requester_access_key = action.requester_access_key

        template_info = await self._session_repository.get_template_info_by_id(template_id)
        if not template_info:
            raise TaskTemplateNotFound
        template = template_info["template"]

        group_name = None
        if template_info["domain_name"] and template_info["group_id"]:
            group_name = await self._session_repository.get_group_name_by_domain_and_id(
                template_info["domain_name"], template_info["group_id"]
            )

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
            raise InvalidAPIParameters("Error while validating template") from e1
        except t.DataError as e2:
            log.debug("Error: {0}", str(e2))
            raise InvalidAPIParameters("Error while validating template") from e2
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
        is_preemptible = params.get("is_preemptible", True)
        bootstrap_script = params["bootstrap_script"]
        dependencies = params["dependencies"]
        startup_command = params["startup_command"]
        starts_at = params["starts_at"]
        batch_timeout = params["batch_timeout"]
        callback_url = params["callback_url"]
        reuse_if_exists = params["reuse_if_exists"]
        domain_name = params["domain_name"]

        user_info = await self._session_repository.query_userinfo(
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
            image_row = await self._session_repository.resolve_image([
                ImageIdentifier(
                    image,
                    architecture,
                ),
                ImageAlias(image),
            ])

            resp = await self._agent_registry.create_session(
                session_name,
                image_row.image_ref,
                UserScope(
                    domain_name=domain_name,
                    group_id=user_info.group_id,
                    user_uuid=user_info.owner_uuid,
                    user_role=user_info.owner_role.value,
                ),
                owner_access_key,
                user_info.resource_policy,
                session_type,
                config,
                cluster_mode,
                cluster_size,
                reuse=reuse_if_exists,
                priority=priority,
                is_preemptible=is_preemptible,
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
        except UnknownImageReference as e:
            raise UnknownImageReferenceError(f"Unknown image reference: {image}") from e
        except BackendAIError:
            raise
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": user_info.owner_uuid})
            log.exception("GET_OR_CREATE: unexpected error!", e)
            raise InternalServerError from e

    async def destroy_session(self, action: DestroySessionAction) -> DestroySessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        forced = action.forced
        recursive = action.recursive

        # Get session IDs to terminate (based on recursive flag)
        session_ids = await self._session_repository.get_target_session_ids(
            session_name,
            owner_access_key,
            recursive=recursive,
        )

        # Determine termination reason based on forced flag
        if forced:
            reason = KernelLifecycleEventReason.FORCE_TERMINATED
        else:
            reason = KernelLifecycleEventReason.USER_REQUESTED

        # Mark sessions for termination
        mark_result = await self._scheduling_controller.mark_sessions_for_termination(
            session_ids,
            reason=reason.value,
            forced=forced,
        )

        # Build stats for response - prioritize cancelled over terminating/force-terminated
        if mark_result.cancelled_sessions:
            last_stat = {"status": "cancelled"}
        elif mark_result.terminating_sessions or mark_result.force_terminated_sessions:
            last_stat = {"status": "terminated"}
        else:
            last_stat = {}

        # Return response - same format for both recursive and non-recursive
        resp = {"stats": last_stat}
        return DestroySessionActionResult(result=resp, session_ids=list(session_ids))

    async def terminate_sessions(
        self, action: TerminateSessionsAction
    ) -> TerminateSessionsActionResult:
        """Terminate multiple sessions by their IDs."""
        reason = (
            KernelLifecycleEventReason.FORCE_TERMINATED
            if action.forced
            else KernelLifecycleEventReason.USER_REQUESTED
        )
        mark_result = await self._scheduling_controller.mark_sessions_for_termination(
            action.session_ids, reason=reason.value, forced=action.forced
        )
        return TerminateSessionsActionResult(
            cancelled=mark_result.cancelled_sessions,
            terminating=mark_result.terminating_sessions,
            force_terminated=mark_result.force_terminated_sessions,
            skipped=mark_result.skipped_sessions,
        )

    async def download_file(self, action: DownloadFileAction) -> DownloadFileActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        user_id = action.user_id
        file = action.file
        try:
            session = await self._session_repository.get_session_validated(
                session_name,
                owner_access_key,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
            result = await self._agent_registry.download_single(session, owner_access_key, file)
        except (ValueError, FileNotFoundError) as e:
            raise InvalidAPIParameters("The file is not found.") from e
        except asyncio.CancelledError:
            raise
        except BackendAIError:
            raise
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("DOWNLOAD_SINGLE: unexpected error!", e)
            raise InternalServerError from e

        return DownloadFileActionResult(bytes=result, session_data=session.to_dataclass())

    async def download_files(self, action: DownloadFilesAction) -> DownloadFilesActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        user_id = action.user_id
        files = action.files
        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        try:
            if len(files) > 5:
                raise VFolderBadRequest("Too many files (maximum 5 files allowed)")
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
            raise
        except (ValueError, FileNotFoundError) as e:
            raise InvalidAPIParameters("The file is not found.") from e
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("DOWNLOAD_FILE: unexpected error!", e)
            raise InternalServerError from e

        with aiohttp.MultipartWriter("mixed") as mpwriter:
            headers = multidict.MultiDict({"Content-Encoding": "identity"})
            for tarbytes in results:
                mpwriter.append(tarbytes, headers)

            return DownloadFilesActionResult(
                session_data=session.to_dataclass(),
                result=mpwriter,
            )

    async def execute_session(self, action: ExecuteSessionAction) -> ExecuteSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        api_version = action.api_version

        resp = {}
        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        try:
            run_id: str | None
            mode: str | None

            if api_version[0] == 1:
                run_id = action.params.run_id or secrets.token_hex(8)
                mode = "query"
                code = action.params.code
                opts = None
            elif api_version[0] >= 2:
                run_id = action.params.run_id
                mode = action.params.mode

                if mode is None:
                    raise InvalidSessionData("runId or mode is missing")

                if mode not in {"query", "batch", "complete", "continue", "input"}:
                    raise InvalidSessionData(f"mode has an invalid value: {mode}")
                if mode in {"continue", "input"} and run_id is None:
                    raise InvalidSessionData("continuation requires explicit run ID")
                code = action.params.code
                opts = action.params.options
            else:
                raise RuntimeError("should not reach here")
            # handle cases when some params are deliberately set to None
            if code is None:
                code = ""
            if opts is None:
                opts = {}
            if mode == "complete":
                # For legacy
                completion_resp = await self._agent_registry.get_completions(session, code, opts)
                resp["result"] = completion_resp.as_dict()
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
            raise InvalidAPIParameters(extra_msg=e.args[0]) from e
        except BackendAIError:
            raise

        return ExecuteSessionActionResult(result=resp, session_data=session.to_dataclass())

    async def get_abusing_report(
        self, action: GetAbusingReportAction
    ) -> GetAbusingReportActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        kernel = session.main_kernel
        report = await self._agent_registry.get_abusing_report(kernel.id)
        return GetAbusingReportActionResult(
            abuse_report=report, session_data=session.to_dataclass()
        )

    async def get_commit_status(self, action: GetCommitStatusAction) -> GetCommitStatusActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        statuses = await self._agent_registry.get_commit_status([session.main_kernel.id])

        commit_info = CommitStatusInfo(
            status=statuses[session.main_kernel.id], kernel=str(session.main_kernel.id)
        )
        return GetCommitStatusActionResult(
            commit_info=commit_info, session_data=session.to_dataclass()
        )

    async def get_container_logs(
        self, action: GetContainerLogsAction
    ) -> GetContainerLogsActionResult:
        resp = {"result": {"logs": ""}}
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        kernel_id = action.kernel_id

        compute_session = await self._session_repository.get_session_validated(
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
                return GetContainerLogsActionResult(
                    result=resp, session_data=compute_session.to_dataclass()
                )

        registry = self._agent_registry
        resp["result"]["logs"] = await registry.get_logs_from_agent(
            session=compute_session, kernel_id=kernel_id
        )
        log.debug("returning log from agent")

        return GetContainerLogsActionResult(
            result=resp, session_data=compute_session.to_dataclass()
        )

    async def get_dependency_graph(
        self, action: GetDependencyGraphAction
    ) -> GetDependencyGraphActionResult:
        root_session_name = action.root_session_name
        owner_access_key = action.owner_access_key

        dependency_graph = await self._session_repository.find_dependency_sessions(
            root_session_name, owner_access_key
        )

        session_id = (
            dependency_graph.get("session_id") if isinstance(dependency_graph, dict) else None
        )
        if session_id:
            if isinstance(session_id, list) and session_id:
                session_id = session_id[0]
            session = await self._session_repository.get_session_by_id(str(session_id))
        else:
            session = None

        if session is None:
            raise SessionNotFound
        return GetDependencyGraphActionResult(
            result=dependency_graph, session_data=session.to_dataclass()
        )

    async def get_direct_access_info(
        self, action: GetDirectAccessInfoAction
    ) -> GetDirectAccessInfoActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        sess = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        resp = {}
        sess_type = sess.session_type
        if sess_type in PRIVATE_SESSION_TYPES:
            if sess.main_kernel.agent_row is None:
                raise KernelNotReady(
                    f"Kernel of the session has no agent info yet (kernel: {sess.main_kernel.id}, kernel status: {sess.main_kernel.status.name})"
                )
            public_host = sess.main_kernel.agent_row.public_host
            found_ports: dict[str, list[str]] = {}
            service_ports = sess.main_kernel.service_ports
            if service_ports is None:
                raise KernelNotReady(
                    f"Kernel of the session has no service ports yet (kernel: {sess.main_kernel.id}, kernel status: {sess.main_kernel.status.name})"
                )
            for sport in service_ports:
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

        return GetDirectAccessInfoActionResult(result=resp, session_data=sess.to_dataclass())

    async def get_session_info(self, action: GetSessionInfoAction) -> GetSessionInfoActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        sess = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )

        created_at = sess.created_at or datetime.now(tzutc())
        age = datetime.now(tzutc()) - created_at
        session_info = LegacySessionInfo(
            domain_name=sess.domain_name,
            group_id=sess.group_id,
            user_id=sess.user_uuid,
            lang=sess.main_kernel.image or "",  # legacy
            image=sess.main_kernel.image or "",
            architecture=sess.main_kernel.architecture or "",
            registry=sess.main_kernel.registry,
            tag=sess.tag,
            container_id=ContainerId(sess.main_kernel.container_id)
            if sess.main_kernel.container_id
            else None,
            occupied_slots=str(sess.main_kernel.occupied_slots),  # legacy
            occupying_slots=str(sess.occupying_slots),
            requested_slots=str(sess.requested_slots),
            occupied_shares=str(sess.main_kernel.occupied_shares),  # legacy
            environ=str(sess.environ),
            resource_opts=str(sess.resource_opts),
            status=sess.status,
            status_info=str(sess.status_info) if sess.status_info else None,
            status_data=sess.status_data,
            age_ms=int(age.total_seconds() * 1000),
            creation_time=created_at,
            termination_time=sess.terminated_at,
            num_queries_executed=sess.num_queries or 0,
            last_stat=sess.last_stat,
            idle_checks=await self._idle_checker_host.get_idle_check_report(sess.id),
        )

        # Resource limits collected from agent heartbeats were erased, as they were deprecated
        # TODO: factor out policy/image info as a common repository
        return GetSessionInfoActionResult(
            session_info=session_info, session_data=sess.to_dataclass()
        )

    async def get_status_history(
        self, action: GetStatusHistoryAction
    ) -> GetStatusHistoryActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        session_row = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.NONE,
        )
        result = session_row.status_history or {}

        return GetStatusHistoryActionResult(status_history=result, session_id=session_row.id)

    async def interrupt(self, action: InterruptSessionAction) -> InterruptSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        await self._agent_registry.interrupt_session(session)

        return InterruptSessionActionResult(result=None, session_data=session.to_dataclass())

    async def list_files(self, action: ListFilesAction) -> ListFilesActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        user_id = action.user_id
        path = action.path

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )

        resp: MutableMapping[str, Any] = {}
        try:
            result = await self._agent_registry.list_files(session, path)
            resp.update(result)
            log.debug("container file list for {0} retrieved", path)
        except asyncio.CancelledError:
            raise
        except BackendAIError:
            raise
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("LIST_FILES: unexpected error!", e)
            raise InternalServerError from e

        return ListFilesActionResult(result=result, session_data=session.to_dataclass())

    async def match_sessions(self, action: MatchSessionsAction) -> MatchSessionsActionResult:
        id_or_name_prefix = action.id_or_name_prefix
        owner_access_key = action.owner_access_key

        matches: list[dict[str, Any]] = []
        sessions = await self._session_repository.match_sessions(
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

        try:
            compute_session = await self._session_repository.update_session_name(
                session_name, new_name, owner_access_key
            )
            if compute_session.status != SessionStatus.RUNNING:
                raise InvalidAPIParameters("Can't change name of not running session")
        except ValueError as e:
            if "already exists" in str(e):
                raise InvalidAPIParameters(str(e)) from e
            raise

        return RenameSessionActionResult(session_data=compute_session.to_dataclass())

    async def shutdown_service(self, action: ShutdownServiceAction) -> ShutdownServiceActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        service_name = action.service_name

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        await self._agent_registry.shutdown_service(session, service_name)
        return ShutdownServiceActionResult(result=None, session_data=session.to_dataclass())

    async def start_service(self, action: StartServiceAction) -> StartServiceActionResult:
        session_id = action.session_id
        service = action.service
        port = action.port

        arguments = action.arguments
        envs = action.envs
        login_session_token = action.login_session_token

        info = await self._session_repository.get_session_with_routing_minimal(session_id)
        session_data = info.session

        if session_data.scaling_group_name is None:
            raise ServiceUnavailable("Session has no scaling group assigned")
        wsproxy_addr = await self._session_repository.get_scaling_group_wsproxy_addr(
            session_data.scaling_group_name
        )
        if not wsproxy_addr:
            raise ServiceUnavailable("No coordinator configured for this resource group")
        client = self._appproxy_client_pool.load_client(wsproxy_addr, "")
        wsproxy_status = await client.fetch_status()
        if wsproxy_status.advertise_address:
            wsproxy_advertise_addr = wsproxy_status.advertise_address
        else:
            wsproxy_advertise_addr = wsproxy_addr

        if info.kernel_host is None:
            kernel_host = urlparse(info.agent_addr).hostname
        else:
            kernel_host = info.kernel_host
        service_ports: list[dict[str, Any]] = info.service_ports
        sport: dict[str, Any] = {}
        host_port: int
        for sport in service_ports:
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
                    except ValueError as e:
                        raise InvalidAPIParameters(
                            f"Service {service} does not open the port number {port}."
                        ) from e
                    host_port = sport["host_ports"][hport_idx]
                else:
                    # using the default (primary) port of the app
                    if "host_ports" not in sport:
                        host_port = sport["host_port"]  # legacy kernels
                    else:
                        host_port = sport["host_ports"][0]
                break
        else:
            raise AppNotFound(f"{session_data.name}:{service}")

        opts: MutableMapping[str, None | str | list[str]] = {}
        if arguments is not None:
            opts["arguments"] = load_json(arguments)
        if envs is not None:
            opts["envs"] = load_json(envs)

        if info.agent_id is None:
            raise AgentNotAllocated(f"Session {session_id} main kernel has no agent allocated")
        result = await asyncio.shield(
            self._rpc_ptask_group.create_task(
                self._agent_registry.start_service(
                    info.main_kernel_id, info.agent_id, service, opts
                ),
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
                "id": str(session_data.id),
                "user_uuid": str(session_data.user_uuid),
                "group_id": str(session_data.group_id),
                "access_key": session_data.access_key,
                "domain_name": session_data.domain_name,
            },
        }

        async with (
            aiohttp.ClientSession() as req,
            req.post(
                f"{wsproxy_addr}/v2/conf",
                json=body,
            ) as resp,
        ):
            token_json = await resp.json()

            return StartServiceActionResult(
                result=None,
                session_data=session_data,
                token=token_json["token"],
                wsproxy_addr=wsproxy_advertise_addr,
            )

    async def upload_files(self, action: UploadFilesAction) -> UploadFilesActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key
        reader = action.reader

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )

        file_count = 0

        async with aiotools.TaskScope() as ts:
            async for file in aiotools.aiter(reader.next, None):
                if file_count == 20:
                    raise InvalidAPIParameters("Too many files")
                if file is None:
                    break
                if not isinstance(file, BodyPartReader):
                    raise InvalidAPIParameters("Nested multipart upload is not supported")
                file_name = file.filename or f"upload-{secrets.token_hex(12)}"
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
                log.debug("received file: {0} ({1:,} bytes)", file_name, recv_size)
                ts.create_task(self._agent_registry.upload_file(session, file_name, data))

        return UploadFilesActionResult(result=None, session_data=session.to_dataclass())

    async def get_session(self, action: GetSessionAction) -> GetSessionActionResult:
        """Get a single session by ID with RBAC validation."""
        session_data = await self._session_repository.get_session_data_by_id(
            action.session_id,
        )
        return GetSessionActionResult(session_data=session_data)

    async def modify_session(self, action: ModifySessionAction) -> ModifySessionActionResult:
        session_id = action.session_id
        spec = cast(SessionUpdaterSpec, action.updater.spec)
        session_name = spec.name.optional_value()

        session_row = await self._session_repository.modify_session(action.updater, session_name)
        if session_row is None:
            raise ValueError(f"Session not found (id:{session_id})")
        session_owner_data = await self._session_repository.get_session_owner(str(session_id))

        return ModifySessionActionResult(
            session_data=session_row.to_dataclass(owner=session_owner_data)
        )

    async def search(self, action: SearchSessionsAction) -> SearchSessionsActionResult:
        """Search sessions with querier pattern."""
        result = await self._session_repository.search(action.querier)
        return SearchSessionsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_in_project(
        self, action: SearchSessionsInProjectAction
    ) -> SearchSessionsInProjectActionResult:
        """Search sessions scoped to a project."""
        result = await self._session_repository.search_in_project(action.querier, action.scope)
        return SearchSessionsInProjectActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_kernels(self, action: SearchKernelsAction) -> SearchKernelsActionResult:
        """Search kernels with querier pattern."""
        result = await self._session_repository.search_kernels(action.querier)
        return SearchKernelsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def enqueue_session(self, action: EnqueueSessionAction) -> EnqueueSessionActionResult:
        """Enqueue a new compute session (PENDING) through the scheduler.

        Builds a :class:`SessionSpecDraft` inline from the caller-supplied
        action, resolves delegation (``action.owner_id``), and hands the
        draft straight to the scheduling controller. The controller owns
        every DB read the preparer / validator chain needs — this
        service just extracts values from the action and shapes them
        into the draft.
        """
        user_id = action.user_id
        access_key = action.access_key
        domain_name = action.domain_name
        if action.owner_id is not None:
            owner = await self._user_repository.get_user_by_uuid(action.owner_id)
            if owner.main_access_key is None:
                raise InternalServerError(
                    f"Delegated owner {action.owner_id} has no main access key configured"
                )
            if owner.role is None:
                raise InternalServerError(
                    f"Delegated owner {action.owner_id} has no role configured"
                )
            if owner.domain_name is None:
                raise InternalServerError(
                    f"Delegated owner {action.owner_id} has no domain configured"
                )
            user_id = owner.id
            access_key = AccessKey(owner.main_access_key)
            domain_name = owner.domain_name

        # Keep the image resolve so callers passing a stale UUID get a
        # sharp error here instead of deep inside the preparer chain.
        await self._session_repository.resolve_image_by_id(action.image_id)

        resource_entries = tuple(
            ResourceSlotEntry(resource_type=entry.resource_type, quantity=entry.quantity)
            for entry in action.resource.entries
        )
        resource_opts_payload: dict[str, Any] = {}
        if action.resource.shmem is not None:
            resource_opts_payload["shmem"] = BinarySize.from_str(action.resource.shmem)
        resource_opts = ResourceOpts.model_validate(resource_opts_payload)

        mount_entries = tuple(action.mounts or ())

        environ: dict[str, str] = (
            dict(action.execution.environ) if action.execution and action.execution.environ else {}
        )
        preopen_ports = tuple(action.execution.preopen_ports or ()) if action.execution else ()
        bootstrap_script = action.execution.bootstrap_script if action.execution else None
        startup_command = action.batch.startup_command if action.batch else None
        starts_at = action.batch.starts_at if action.batch else None
        batch_timeout_sec = (
            int(action.batch.batch_timeout.total_seconds())
            if action.batch and action.batch.batch_timeout is not None
            else None
        )

        dependencies = tuple(SessionID(dep_id) for dep_id in (action.scheduling.dependencies or ()))
        callback_url = yarl.URL(action.callback_url) if action.callback_url else None

        if action.resource.resource_group:
            resource_group_name = ResourceGroupName(action.resource.resource_group)
        else:
            resource_group_name = await self._scheduler_repository.pick_default_resource_group(
                access_key=access_key,
                domain_name=domain_name,
                project_id=ProjectID(action.group_id),
            )
        kernel_groups = await self._resolve_kernel_groups(
            cluster_size=action.resource.cluster_size,
            preopen_ports=preopen_ports,
            execution_spec=KernelExecutionSpecDraft(
                image_id=ImageID(action.image_id),
                resources=resource_entries,
                resource_opts=resource_opts,
                environ=environ,
                mounts=mount_entries,
                startup_command=startup_command,
                bootstrap_script=bootstrap_script,
                starts_at=starts_at,
                batch_timeout_sec=batch_timeout_sec,
            ),
        )

        draft = SessionSpecDraft(
            identity=SessionIdentityDraft(
                session_id=SessionID(uuid.uuid4()),
                creation_id=secrets.token_urlsafe(16),
                session_name=action.session_name,
                access_key=access_key,
                user_uuid=user_id,
            ),
            scope=SessionScopeDraft(
                domain_name=DomainName(domain_name),
                project_id=ProjectID(action.group_id),
                resource_group_name=resource_group_name,
            ),
            classification=SessionClassificationDraft(
                session_type=action.session_type,
                tag=action.tag,
            ),
            network=SessionNetworkDraft(
                network_id=(
                    str(action.scheduling.attach_network)
                    if action.scheduling.attach_network is not None
                    else None
                ),
            ),
            callback_url=callback_url,
            dependencies=dependencies,
            options=SessionOptionsDraft(
                priority=action.scheduling.priority or SESSION_PRIORITY_DEFAULT,
                is_preemptible=action.scheduling.is_preemptible,
                cluster_mode=action.resource.cluster_mode,
                cluster_size=action.resource.cluster_size,
                scheduling_target=SchedulingTargetDraft(
                    designated_agents=tuple(
                        AgentId(a) for a in (action.scheduling.agent_list or ())
                    ),
                ),
                kernel_groups=kernel_groups,
                handler_options=SessionHandlerOptions(),
            ),
            internal_data_extras=InternalDataExtras(
                sudo_session_enabled=False,
            ),
        )

        session_id = await self._scheduling_controller.enqueue_session_from_draft(draft)

        session_data = await self._session_repository.get_session_data_by_id(session_id)

        return EnqueueSessionActionResult(session_data=session_data)

    async def _resolve_kernel_groups(
        self,
        cluster_size: int,
        preopen_ports: tuple[int, ...],
        execution_spec: KernelExecutionSpecDraft,
    ) -> tuple[KernelGroupDraft, ...]:
        # 1 main + (cluster_size - 1) sub, matching legacy registry Shape (a).
        groups: tuple[KernelGroupDraft, ...] = (
            KernelGroupDraft(
                role=DEFAULT_ROLE,
                replica_count=1,
                preopen_ports=preopen_ports,
                execution_spec=execution_spec,
            ),
        )
        if cluster_size > 1:
            groups += (
                KernelGroupDraft(
                    role="sub",
                    replica_count=cluster_size - 1,
                    preopen_ports=preopen_ports,
                    execution_spec=execution_spec,
                ),
            )
        return groups
