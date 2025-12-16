import asyncio
import base64
import functools
import logging
import secrets
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping, MutableMapping, Optional, Union, cast
from urllib.parse import urlparse

import aiohttp
import aiotools
import multidict
import trafaret as t
from aiohttp.multipart import BodyPartReader
from dateutil.tz import tzutc

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.exception import (
    BackendAIError,
    InvalidAPIParameters,
    UnknownImageReference,
)
from ai.backend.common.json import load_json
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.common.types import (
    ImageAlias,
    SessionId,
    SessionTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.scaling_group import query_wsproxy_status
from ai.backend.manager.api.session import (
    CustomizedImageVisibilityScope,
    drop_undefined,
    overwritten_param_check,
)
from ai.backend.manager.api.utils import undefined
from ai.backend.manager.bgtask.tasks.commit_session import CommitSessionManifest
from ai.backend.manager.bgtask.types import ManagerBgtaskName
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.session.types import SessionStatus
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
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.session.admin_repository import AdminSessionRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.session.updaters import SessionUpdaterSpec
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
from ai.backend.manager.services.session.types import CommitStatusInfo, LegacySessionInfo
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import UserScope

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


@dataclass
class SessionServiceArgs:
    agent_registry: AgentRegistry
    event_fetcher: EventFetcher
    background_task_manager: BackgroundTaskManager
    event_hub: EventHub
    error_monitor: ErrorPluginContext
    idle_checker_host: IdleCheckerHost
    session_repository: SessionRepository
    admin_session_repository: AdminSessionRepository
    scheduling_controller: SchedulingController


class SessionService:
    _agent_registry: AgentRegistry
    _background_task_manager: BackgroundTaskManager
    _event_fetcher: EventFetcher
    _event_hub: EventHub
    _error_monitor: ErrorPluginContext
    _idle_checker_host: IdleCheckerHost
    _session_repository: SessionRepository
    _admin_session_repository: AdminSessionRepository
    _scheduling_controller: SchedulingController
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
        self._admin_session_repository = args.admin_session_repository
        self._scheduling_controller = args.scheduling_controller
        self._database_ptask_group = aiotools.PersistentTaskGroup()
        self._rpc_ptask_group = aiotools.PersistentTaskGroup()
        self._webhook_ptask_group = aiotools.PersistentTaskGroup()

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
            await self._agent_registry.increment_session_usage(session)
            resp = await self._agent_registry.get_completions(session, code, opts=options)
        except AssertionError:
            raise InvalidAPIParameters
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
        await self._session_repository.resolve_image([
            ImageIdentifier(session.main_kernel.image, session.main_kernel.architecture)
        ])

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
            _, group_id, resource_policy = await self._session_repository.query_userinfo(
                user_id,
                requester_access_key,
                user_role,
                domain_name,
                keypair_resource_policy,
                domain_name,
                group_name,
                query_on_behalf_of=(None if owner_access_key is undefined else owner_access_key),
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
            raise
        except UnknownImageReference:
            raise UnknownImageReferenceError("Unknown image reference!")
        except Exception as e:
            await self._error_monitor.capture_exception()
            log.exception("GET_OR_CREATE: unexpected error!", e)
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

        owner_uuid, group_id, resource_policy = await self._session_repository.query_userinfo(
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
            return CreateFromParamsActionResult(
                session_id=uuid.UUID(resp["sessionId"]), result=resp
            )
        except UnknownImageReference:
            raise UnknownImageReferenceError(f"Unknown image reference: {image}")
        except BackendAIError:
            raise
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": owner_uuid})
            log.exception("GET_OR_CREATE: unexpected error!", e)
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
            raise InvalidAPIParameters("Error while validating template")
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

        owner_uuid, group_id, resource_policy = await self._session_repository.query_userinfo(
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
            raise
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": owner_uuid})
            log.exception("GET_OR_CREATE: unexpected error!", e)
            raise InternalServerError

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
        )

        # Build stats for response - prioritize cancelled over terminating
        if mark_result.cancelled_sessions:
            last_stat = {"status": "cancelled"}
        elif mark_result.terminating_sessions:
            last_stat = {"status": "terminated"}
        else:
            last_stat = {}

        # Return response - same format for both recursive and non-recursive
        resp = {"stats": last_stat}
        return DestroySessionActionResult(result=resp)

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
            await self._agent_registry.increment_session_usage(session)
            result = await self._agent_registry.download_single(session, owner_access_key, file)
        except (ValueError, FileNotFoundError):
            raise InvalidAPIParameters("The file is not found.")
        except asyncio.CancelledError:
            raise
        except BackendAIError:
            raise
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("DOWNLOAD_SINGLE: unexpected error!", e)
            raise InternalServerError

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
            raise
        except (ValueError, FileNotFoundError):
            raise InvalidAPIParameters("The file is not found.")
        except Exception as e:
            await self._error_monitor.capture_exception(context={"user": user_id})
            log.exception("DOWNLOAD_FILE: unexpected error!", e)
            raise InternalServerError

        with aiohttp.MultipartWriter("mixed") as mpwriter:
            headers = multidict.MultiDict({"Content-Encoding": "identity"})
            for tarbytes in results:
                mpwriter.append(tarbytes, headers)

            return DownloadFilesActionResult(
                session_data=session.to_dataclass(),
                result=mpwriter,  # type: ignore
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
                code = ""  # noqa
            if opts is None:
                opts = {}  # noqa
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
                    return ExecuteSessionActionResult(
                        result=resp, session_data=session.to_dataclass()
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
            raise InvalidAPIParameters(extra_msg=e.args[0])
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
        await registry.increment_session_usage(compute_session)
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
        sess_type = cast(SessionTypes, sess.session_type)
        if sess_type in PRIVATE_SESSION_TYPES:
            public_host = sess.main_kernel.agent_row.public_host
            found_ports: dict[str, list[str]] = {}
            service_ports = cast(Optional[list[dict[str, Any]]], sess.main_kernel.service_ports)
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
        await self._agent_registry.increment_session_usage(sess)

        age = datetime.now(tzutc()) - sess.created_at
        session_info = LegacySessionInfo(
            domain_name=sess.domain_name,
            group_id=sess.group_id,
            user_id=sess.user_uuid,
            lang=sess.main_kernel.image,  # legacy
            image=sess.main_kernel.image,
            architecture=sess.main_kernel.architecture,
            registry=sess.main_kernel.registry,
            tag=sess.tag,
            container_id=sess.main_kernel.container_id,
            occupied_slots=str(sess.main_kernel.occupied_slots),  # legacy
            occupying_slots=str(sess.occupying_slots),
            requested_slots=str(sess.requested_slots),
            occupied_shares=str(sess.main_kernel.occupied_shares),  # legacy
            environ=str(sess.environ),
            resource_opts=str(sess.resource_opts),
            status=sess.status.name,
            status_info=str(sess.status_info) if sess.status_info else None,
            status_data=sess.status_data,
            age_ms=int(age.total_seconds() * 1000),
            creation_time=sess.created_at,
            termination_time=sess.terminated_at,
            num_queries_executed=sess.num_queries,
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
        result = session_row.status_history

        return GetStatusHistoryActionResult(status_history=result, session_id=session_row.id)

    async def interrupt(self, action: InterruptSessionAction) -> InterruptSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        await self._agent_registry.increment_session_usage(session)
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
            await self._agent_registry.increment_session_usage(session)
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
            raise InternalServerError

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
                raise InvalidAPIParameters(str(e))
            raise

        return RenameSessionActionResult(session_data=compute_session.to_dataclass())

    async def restart_session(self, action: RestartSessionAction) -> RestartSessionActionResult:
        session_name = action.session_name
        owner_access_key = action.owner_access_key

        session = await self._session_repository.get_session_validated(
            session_name,
            owner_access_key,
            kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS,
        )
        await self._agent_registry.increment_session_usage(session)
        await self._agent_registry.restart_session(session)
        return RestartSessionActionResult(result=None, session_data=session.to_dataclass())

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
        session_name = action.session_name
        access_key = action.access_key
        service = action.service
        port = action.port

        arguments = action.arguments
        envs = action.envs
        login_session_token = action.login_session_token

        session = await asyncio.shield(
            self._database_ptask_group.create_task(
                self._session_repository.get_session_with_routing_minimal(
                    session_name,
                    access_key,
                )
            )
        )

        wsproxy_addr = await self._session_repository.get_scaling_group_wsproxy_addr(
            session.scaling_group_name
        )
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
                    session_data=session.to_dataclass(),
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

        await self._agent_registry.increment_session_usage(session)
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

    async def check_and_transit_status(
        self, action: CheckAndTransitStatusAction
    ) -> CheckAndTransitStatusActionResult:
        user_id = action.user_id
        user_role = action.user_role
        session_id = action.session_id

        if user_role in (UserRole.ADMIN, UserRole.SUPERADMIN):
            session_row = (
                await self._admin_session_repository.get_session_to_determine_status_force(
                    session_id
                )
            )
        else:
            session_row = await self._session_repository.get_session_to_determine_status(session_id)
            if session_row.user_uuid != user_id:
                log.warning(
                    f"You are not allowed to transit others's sessions status, skip (s:{session_id})"
                )
                return CheckAndTransitStatusActionResult(
                    result={}, session_data=session_row.to_dataclass()
                )

        now = datetime.now(tzutc())
        session_rows = await self._agent_registry.session_lifecycle_mgr.transit_session_status(
            [session_id], now
        )
        await self._agent_registry.session_lifecycle_mgr.deregister_status_updatable_session([
            row.id for row, is_transited in session_rows if is_transited
        ])
        session_owner_data = await self._session_repository.get_session_owner(session_id)

        result = {row.id: row.status.name for row, _ in session_rows}
        return CheckAndTransitStatusActionResult(
            result=result, session_data=session_row.to_dataclass(owner=session_owner_data)
        )

    async def check_and_transit_status_multi(
        self, action: CheckAndTransitStatusBatchAction
    ) -> CheckAndTransitStatusBatchActionResult:
        user_id = action.user_id
        user_role = action.user_role
        session_ids = action.session_ids
        accessible_session_ids: list[SessionId] = []

        for sid in session_ids:
            if user_role in (UserRole.ADMIN, UserRole.SUPERADMIN):
                accessible_session_ids.append(sid)
            else:
                try:
                    session_row = await self._session_repository.get_session_to_determine_status(
                        sid
                    )
                    if session_row.user_uuid == user_id:
                        accessible_session_ids.append(sid)
                    else:
                        log.warning(
                            f"You are not allowed to transit others's sessions status, skip (s:{sid})"
                        )
                except Exception:
                    log.warning(f"Session not found or access denied, skip (s:{sid})")

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
