"""Session handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``UserContext``, ``RequestCtx``) are
automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, cast
from uuid import UUID

import yarl
from aiohttp import web
from pydantic import BaseModel

from ai.backend.common.api_handlers import APIResponse, BaseResponseModel, BodyParam, QueryParam
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.session.request import (
    CommitSessionRequest,
    CompleteRequest,
    ConvertSessionToImageRequest,
    CreateClusterRequest,
    CreateFromParamsRequest,
    CreateFromTemplateRequest,
    DestroySessionRequest,
    DownloadFilesRequest,
    DownloadSingleRequest,
    ExecuteRequest,
    GetAbusingReportRequest,
    GetCommitStatusRequest,
    GetContainerLogsRequest,
    GetStatusHistoryRequest,
    GetTaskLogsRequest,
    ListFilesRequest,
    MatchSessionsRequest,
    RenameSessionRequest,
    RestartSessionRequest,
    ShutdownServiceRequest,
    StartServiceRequest,
    SyncAgentRegistryRequest,
    TransitSessionStatusRequest,
)
from ai.backend.common.dto.manager.session.response import (
    CommitSessionResponse,
    CompleteResponse,
    ConvertSessionToImageResponse,
    CreateSessionResponse,
    DestroySessionResponse,
    ExecuteResponse,
    GetAbusingReportResponse,
    GetCommitStatusResponse,
    GetContainerLogsResponse,
    GetDependencyGraphResponse,
    GetDirectAccessInfoResponse,
    GetSessionInfoResponse,
    GetStatusHistoryResponse,
    ListFilesResponse,
    MatchSessionsResponse,
    StartServiceResponse,
    TransitSessionStatusResponse,
)
from ai.backend.common.dto.manager.session.types import (
    CreationConfigV1,
    CreationConfigV2,
    CreationConfigV3,
    CreationConfigV3Template,
    CreationConfigV4,
    CreationConfigV4Template,
    CreationConfigV5,
    CreationConfigV5Template,
    CreationConfigV6,
    CreationConfigV6Template,
    CreationConfigV7,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    SessionId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import undefined
from ai.backend.manager.defs import DEFAULT_IMAGE_ARCH
from ai.backend.manager.dto.context import RequestCtx
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.resource import NoCurrentTaskContext
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.agent.actions.sync_agent_registry import (
    SyncAgentRegistryAction,
)
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    ResolveAccessKeyScopeAction,
)
from ai.backend.manager.services.session.actions.check_and_transit_status import (
    CheckAndTransitStatusAction,
)
from ai.backend.manager.services.session.actions.commit_session import (
    CommitSessionAction,
)
from ai.backend.manager.services.session.actions.complete import CompleteAction
from ai.backend.manager.services.session.actions.convert_session_to_image import (
    ConvertSessionToImageAction,
)
from ai.backend.manager.services.session.actions.create_cluster import (
    CreateClusterAction,
)
from ai.backend.manager.services.session.actions.create_from_params import (
    CreateFromParamsAction,
    CreateFromParamsActionParams,
)
from ai.backend.manager.services.session.actions.create_from_template import (
    CreateFromTemplateAction,
    CreateFromTemplateActionParams,
)
from ai.backend.manager.services.session.actions.destroy_session import (
    DestroySessionAction,
)
from ai.backend.manager.services.session.actions.download_file import (
    DownloadFileAction,
)
from ai.backend.manager.services.session.actions.download_files import (
    DownloadFilesAction,
)
from ai.backend.manager.services.session.actions.execute_session import (
    ExecuteSessionAction,
    ExecuteSessionActionParams,
)
from ai.backend.manager.services.session.actions.get_abusing_report import (
    GetAbusingReportAction,
)
from ai.backend.manager.services.session.actions.get_commit_status import (
    GetCommitStatusAction,
)
from ai.backend.manager.services.session.actions.get_container_logs import (
    GetContainerLogsAction,
)
from ai.backend.manager.services.session.actions.get_dependency_graph import (
    GetDependencyGraphAction,
)
from ai.backend.manager.services.session.actions.get_direct_access_info import (
    GetDirectAccessInfoAction,
)
from ai.backend.manager.services.session.actions.get_session_info import (
    GetSessionInfoAction,
)
from ai.backend.manager.services.session.actions.get_status_history import (
    GetStatusHistoryAction,
)
from ai.backend.manager.services.session.actions.interrupt_session import (
    InterruptSessionAction,
)
from ai.backend.manager.services.session.actions.list_files import ListFilesAction
from ai.backend.manager.services.session.actions.match_sessions import (
    MatchSessionsAction,
)
from ai.backend.manager.services.session.actions.rename_session import (
    RenameSessionAction,
)
from ai.backend.manager.services.session.actions.restart_session import (
    RestartSessionAction,
)
from ai.backend.manager.services.session.actions.shutdown_service import (
    ShutdownServiceAction,
)
from ai.backend.manager.services.session.actions.start_service import (
    StartServiceAction,
)
from ai.backend.manager.services.session.actions.upload_files import (
    UploadFilesAction,
)
from ai.backend.manager.services.vfolder.actions.base import GetTaskLogsAction

if TYPE_CHECKING:
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.services.agent.processors import AgentProcessors
    from ai.backend.manager.services.auth.processors import AuthProcessors
    from ai.backend.manager.services.session.processors import SessionProcessors
    from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _validate_creation_config(
    api_version: tuple[int, ...],
    config: dict[str, Any],
    *,
    template: bool = False,
) -> dict[str, Any]:
    """Validate creation config dict against the API-version-appropriate Pydantic model."""
    try:
        model: BaseModel
        if template:
            if api_version[0] >= 8:
                model = CreationConfigV6Template.model_validate(config)
            elif api_version[0] >= 6:
                model = CreationConfigV5Template.model_validate(config)
            elif api_version[0] >= 5:
                model = CreationConfigV4Template.model_validate(config)
            elif api_version >= (4, "20190315"):
                model = CreationConfigV3Template.model_validate(config)
            else:
                model = CreationConfigV3Template.model_validate(config)
        else:
            if api_version[0] >= 9:
                model = CreationConfigV7.model_validate(config)
            elif api_version[0] >= 8:
                model = CreationConfigV6.model_validate(config)
            elif api_version[0] >= 6:
                model = CreationConfigV5.model_validate(config)
            elif api_version[0] >= 5:
                model = CreationConfigV4.model_validate(config)
            elif api_version >= (4, "20190315"):
                model = CreationConfigV3.model_validate(config)
            elif 2 <= api_version[0] <= 4:
                model = CreationConfigV2.model_validate(config)
            elif api_version[0] == 1:
                model = CreationConfigV1.model_validate(config)
            else:
                raise InvalidAPIParameters("API version not supported")
        return model.model_dump(by_alias=False)
    except Exception as e:
        if isinstance(e, InvalidAPIParameters):
            raise
        log.debug("Validation error: {0}", e)
        raise InvalidAPIParameters(
            "Input validation error",
            extra_data={"config": str(e)},
        ) from e


class SessionHandler:
    """Session API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        auth: AuthProcessors,
        session: SessionProcessors,
        agent: AgentProcessors,
        vfolder: VFolderProcessors,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._auth = auth
        self._session = session
        self._agent = agent
        self._vfolder = vfolder
        self._config_provider = config_provider

    # ------------------------------------------------------------------
    # create_from_template (POST /_/create-from-template)
    # ------------------------------------------------------------------

    async def create_from_template(
        self,
        body: BodyParam[CreateFromTemplateRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed

        if params.image is None and params.template_id is None:
            raise InvalidAPIParameters("Both image and template_id can't be None!")

        api_version = request["api_version"]
        validated_config = _validate_creation_config(
            api_version,
            params.config,
            template=True,
        )

        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=params.owner_access_key,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key

        log.info(
            "GET_OR_CREATE (ak:{0}/{1}, img:{2}, s:{3})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
            params.image,
            params.session_name,
        )

        domain_name = params.domain or request["user"]["domain_name"]

        # Use model_fields_set to detect which fields were explicitly provided
        # (equivalent to the old Trafaret ``undefined`` sentinel).
        _set = params.model_fields_set

        result = await self._session.create_from_template.wait_for_complete(
            CreateFromTemplateAction(
                params=CreateFromTemplateActionParams(
                    template_id=params.template_id or UUID(int=0),
                    session_name=(
                        params.session_name
                        if "session_name" in _set and params.session_name is not None
                        else undefined
                    ),
                    image=(
                        params.image if "image" in _set and params.image is not None else undefined
                    ),
                    architecture=(
                        params.architecture
                        if "architecture" in _set and params.architecture is not None
                        else undefined
                    ),
                    session_type=(
                        params.session_type
                        if "session_type" in _set and params.session_type is not None
                        else undefined
                    ),
                    group_name=(
                        params.group if "group" in _set and params.group is not None else undefined
                    ),
                    domain_name=domain_name,
                    cluster_size=params.cluster_size,
                    cluster_mode=params.cluster_mode,
                    config=validated_config,
                    tag=(params.tag if "tag" in _set and params.tag is not None else undefined),
                    enqueue_only=params.enqueue_only,
                    max_wait_seconds=params.max_wait_seconds,
                    reuse_if_exists=params.reuse,
                    startup_command=(params.startup_command if "startup_command" in _set else None),
                    bootstrap_script=(
                        params.bootstrap_script if "bootstrap_script" in _set else undefined
                    ),
                    dependencies=(
                        [UUID(str(d)) for d in params.dependencies] if params.dependencies else None
                    ),
                    callback_url=(yarl.URL(params.callback_url) if params.callback_url else None),
                    priority=params.priority,
                    is_preemptible=params.is_preemptible,
                    starts_at=params.starts_at,
                    batch_timeout=(
                        timedelta(seconds=float(params.batch_timeout))
                        if params.batch_timeout
                        else None
                    ),
                    owner_access_key=owner_access_key,
                ),
                user_id=request["user"]["uuid"],
                user_role=request["user"]["role"],
                requester_access_key=requester_access_key,
                sudo_session_enabled=request["user"]["sudo_session_enabled"],
                keypair_resource_policy=request["keypair"]["resource_policy"],
            )
        )
        return APIResponse.build(HTTPStatus.CREATED, CreateSessionResponse(dict(result.result)))

    # ------------------------------------------------------------------
    # create_from_params (POST / and POST /_/create)
    # ------------------------------------------------------------------

    async def create_from_params(
        self,
        body: BodyParam[CreateFromParamsRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed

        if params.session_name in ["from-template"]:
            raise InvalidAPIParameters(
                f"Requested session ID {params.session_name} is reserved word"
            )

        api_version = request["api_version"]
        validated_config = _validate_creation_config(api_version, params.config)

        agent_list = cast(list[str] | None, validated_config.get("agent_list"))
        if agent_list is not None:
            if (
                request["user"]["role"] != UserRole.SUPERADMIN
                and self._config_provider.config.manager.hide_agents
            ):
                raise InsufficientPrivilege(
                    "You are not allowed to manually assign agents for your session."
                )

        domain_name = params.domain or request["user"]["domain_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=params.owner_access_key,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "GET_OR_CREATE (ak:{0}/{1}, img:{2}, s:{3})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
            params.image,
            params.session_name,
        )
        architecture = params.architecture or DEFAULT_IMAGE_ARCH

        result = await self._session.create_from_params.wait_for_complete(
            CreateFromParamsAction(
                params=CreateFromParamsActionParams(
                    session_name=params.session_name,
                    image=params.image,
                    architecture=architecture,
                    session_type=params.session_type,
                    group_name=params.group,
                    domain_name=domain_name,
                    cluster_size=params.cluster_size,
                    cluster_mode=params.cluster_mode,
                    config=validated_config,
                    tag=params.tag or "",
                    enqueue_only=params.enqueue_only,
                    max_wait_seconds=params.max_wait_seconds,
                    reuse_if_exists=params.reuse,
                    startup_command=params.startup_command,
                    bootstrap_script=params.bootstrap_script,
                    dependencies=(
                        [UUID(str(d)) for d in params.dependencies] if params.dependencies else None
                    ),
                    callback_url=(yarl.URL(params.callback_url) if params.callback_url else None),
                    priority=params.priority,
                    is_preemptible=params.is_preemptible,
                    starts_at=params.starts_at,
                    batch_timeout=(
                        timedelta(seconds=float(params.batch_timeout))
                        if params.batch_timeout
                        else None
                    ),
                    owner_access_key=owner_access_key,
                ),
                user_id=request["user"]["uuid"],
                user_role=request["user"]["role"],
                requester_access_key=requester_access_key,
                sudo_session_enabled=request["user"]["sudo_session_enabled"],
                keypair_resource_policy=request["keypair"]["resource_policy"],
            )
        )
        return APIResponse.build(HTTPStatus.CREATED, CreateSessionResponse(dict(result.result)))

    # ------------------------------------------------------------------
    # create_cluster (POST /_/create-cluster)
    # ------------------------------------------------------------------

    async def create_cluster(
        self,
        body: BodyParam[CreateClusterRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed

        domain_name = params.domain or request["user"]["domain_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=params.owner_access_key,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "CREAT_CLUSTER (ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
            params.session_name,
        )

        result = await self._session.create_cluster.wait_for_complete(
            CreateClusterAction(
                session_name=params.session_name,
                user_id=request["user"]["uuid"],
                user_role=request["user"]["role"],
                domain_name=domain_name,
                group_name=params.group,
                requester_access_key=requester_access_key,
                owner_access_key=owner_access_key,
                scaling_group_name=params.scaling_group or "",
                tag=params.tag or "",
                session_type=params.session_type,
                enqueue_only=params.enqueue_only,
                template_id=params.template_id or UUID(int=0),
                sudo_session_enabled=request["user"]["sudo_session_enabled"],
                max_wait_seconds=params.max_wait_seconds,
                keypair_resource_policy=request["keypair"]["resource_policy"],
            )
        )
        return APIResponse.build(HTTPStatus.CREATED, CreateSessionResponse(dict(result.result)))

    # ------------------------------------------------------------------
    # match_sessions (GET /_/match)
    # ------------------------------------------------------------------

    async def match_sessions(
        self,
        query: QueryParam[MatchSessionsRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = query.parsed
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        user = current_user()
        if user is None:
            raise UserNotFound("User not found in context")
        log.info(
            "MATCH_SESSIONS(ak:{0}/{1}, prefix:{2})",
            requester_access_key,
            owner_access_key,
            params.id,
        )
        result = await self._session.match_sessions.wait_for_complete(
            MatchSessionsAction(
                id_or_name_prefix=params.id,
                owner_access_key=owner_access_key,
                user_id=user.user_id,
            )
        )
        return APIResponse.build(HTTPStatus.OK, MatchSessionsResponse(matches=result.result))

    # ------------------------------------------------------------------
    # sync_agent_registry (POST /_/sync-agent-registry)
    # ------------------------------------------------------------------

    async def sync_agent_registry(
        self,
        body: BodyParam[SyncAgentRegistryRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        agent_id = AgentId(params.agent)
        log.info(
            "SYNC_AGENT_REGISTRY (ak:{}/{}, a:{})",
            requester_access_key,
            owner_access_key,
            agent_id,
        )
        await self._agent.sync_agent_registry.wait_for_complete(
            SyncAgentRegistryAction(agent_id=agent_id)
        )
        return APIResponse.build(HTTPStatus.OK, CreateSessionResponse({}))

    # ------------------------------------------------------------------
    # check_and_transit_status (POST /_/transit-status)
    # ------------------------------------------------------------------

    async def check_and_transit_status(
        self,
        body: BodyParam[TransitSessionStatusRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed
        session_ids = [SessionId(id_) for id_ in params.ids]
        user_role = cast(UserRole, request["user"]["role"])
        user_id = cast(UUID, request["user"]["uuid"])
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "TRANSIT_STATUS (ak:{}/{}, s:{})",
            requester_access_key,
            owner_access_key,
            session_ids,
        )

        session_status_map: dict[SessionId, str] = {}
        for session_id in session_ids:
            result = await self._session.check_and_transit_status.wait_for_complete(
                CheckAndTransitStatusAction(
                    user_id=user_id,
                    user_role=user_role,
                    session_id=session_id,
                )
            )
            session_status_map.update(result.result)
        return APIResponse.build(
            HTTPStatus.OK,
            TransitSessionStatusResponse(session_status_map=session_status_map),
        )

    # ------------------------------------------------------------------
    # get_info (GET /{session_name})
    # ------------------------------------------------------------------

    async def get_info(self, ctx: RequestCtx) -> APIResponse:
        request = ctx.request
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "GET_INFO (ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        try:
            result = await self._session.get_session_info.wait_for_complete(
                GetSessionInfoAction(
                    session_name=session_name,
                    owner_access_key=owner_access_key,
                )
            )
        except BackendAIError:
            log.exception("GET_INFO: exception")
            raise
        resp = GetSessionInfoResponse(root=result.session_info.asdict())
        return APIResponse.build(
            HTTPStatus.OK,
            cast(BaseResponseModel, resp),
        )

    # ------------------------------------------------------------------
    # restart (PATCH /{session_name})
    # ------------------------------------------------------------------

    async def restart(
        self,
        query: QueryParam[RestartSessionRequest],
        ctx: RequestCtx,
    ) -> web.Response:
        request = ctx.request
        params = query.parsed
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=params.owner_access_key,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "RESTART (ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        try:
            await self._session.restart_session.wait_for_complete(
                RestartSessionAction(
                    session_name=session_name,
                    owner_access_key=owner_access_key,
                )
            )
        except BackendAIError:
            log.exception("RESTART: exception")
            raise
        return web.Response(status=HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # destroy (DELETE /{session_name})
    # ------------------------------------------------------------------

    async def destroy(
        self,
        query: QueryParam[DestroySessionRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = query.parsed
        session_name = request.match_info["session_name"]
        user_role = cast(UserRole, request["user"]["role"])
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=params.owner_access_key,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        if requester_access_key != owner_access_key and user_role not in (
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
        ):
            raise InsufficientPrivilege("You are not allowed to force-terminate others's sessions")

        log.info(
            "DESTROY (ak:{0}/{1}, s:{2}, forced:{3}, recursive: {4})",
            requester_access_key,
            owner_access_key,
            session_name,
            params.forced,
            params.recursive,
        )

        result = await self._session.destroy_session.wait_for_complete(
            DestroySessionAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                user_role=user_role,
                forced=params.forced,
                recursive=params.recursive,
            )
        )
        return APIResponse.build(HTTPStatus.OK, DestroySessionResponse(result.result))

    # ------------------------------------------------------------------
    # execute (POST /{session_name})
    # ------------------------------------------------------------------

    async def execute(
        self,
        body: BodyParam[ExecuteRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "EXECUTE(ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            session_name,
        )

        result = await self._session.execute_session.wait_for_complete(
            ExecuteSessionAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                api_version=request["api_version"],
                params=ExecuteSessionActionParams(
                    mode=params.mode,
                    run_id=params.run_id,
                    code=params.code,
                    options=params.options,
                ),
            )
        )
        return APIResponse.build(HTTPStatus.OK, ExecuteResponse(result.result))

    # ------------------------------------------------------------------
    # interrupt (POST /{session_name}/interrupt)
    # ------------------------------------------------------------------

    async def interrupt(self, ctx: RequestCtx) -> web.Response:
        request = ctx.request
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "INTERRUPT(ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        try:
            await self._session.interrupt.wait_for_complete(
                InterruptSessionAction(
                    session_name=session_name,
                    owner_access_key=owner_access_key,
                )
            )
        except BackendAIError:
            log.exception("INTERRUPT: exception")
            raise
        return web.Response(status=HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # complete (POST /{session_name}/complete)
    # ------------------------------------------------------------------

    async def complete(
        self,
        body: BodyParam[CompleteRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "COMPLETE(ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            session_name,
        )

        action_result = await self._session.complete.wait_for_complete(
            CompleteAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                code=params.code or "",
                options=params.options or {},
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            CompleteResponse(action_result.result.as_dict()),
        )

    # ------------------------------------------------------------------
    # start_service (POST /{session_name}/start-service)
    # ------------------------------------------------------------------

    async def start_service(
        self,
        body: BodyParam[StartServiceRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = body.parsed
        session_name: str = request.match_info["session_name"]
        access_key: AccessKey = request["keypair"]["access_key"]
        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current task context")
        result = await self._session.start_service.wait_for_complete(
            StartServiceAction(
                session_name=session_name,
                access_key=access_key,
                service=params.app,
                login_session_token=params.login_session_token,
                port=params.port,
                envs=params.envs,
                arguments=params.arguments,
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            StartServiceResponse(token=result.token, wsproxy_addr=result.wsproxy_addr),
        )

    # ------------------------------------------------------------------
    # shutdown_service (POST /{session_name}/shutdown-service)
    # ------------------------------------------------------------------

    async def shutdown_service(
        self,
        body: BodyParam[ShutdownServiceRequest],
        ctx: RequestCtx,
    ) -> web.Response:
        request = ctx.request
        params = body.parsed
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "SHUTDOWN_SERVICE (ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        try:
            await self._session.shutdown_service.wait_for_complete(
                ShutdownServiceAction(
                    session_name=session_name,
                    owner_access_key=owner_access_key,
                    service_name=params.service_name,
                )
            )
        except BackendAIError:
            log.exception("SHUTDOWN_SERVICE: exception")
            raise
        return web.Response(status=HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # upload_files (POST /{session_name}/upload)
    # ------------------------------------------------------------------

    async def upload_files(self, ctx: RequestCtx) -> web.Response:
        request = ctx.request
        reader = await request.multipart()
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "UPLOAD_FILE (ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        try:
            await self._session.upload_files.wait_for_complete(
                UploadFilesAction(
                    session_name=session_name,
                    owner_access_key=owner_access_key,
                    reader=reader,
                )
            )
        except BackendAIError:
            log.exception("UPLOAD_FILES: exception")
            raise
        return web.Response(status=HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # download_files (POST /{session_name}/download)
    # ------------------------------------------------------------------

    async def download_files(
        self,
        body: BodyParam[DownloadFilesRequest],
        ctx: RequestCtx,
    ) -> web.Response:
        request = ctx.request
        params = body.parsed
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "DOWNLOAD_FILE (ak:{0}/{1}, s:{2}, path:{3!r})",
            requester_access_key,
            owner_access_key,
            session_name,
            params.files[0],
        )
        result = await self._session.download_files.wait_for_complete(
            DownloadFilesAction(
                user_id=request["user"]["uuid"],
                owner_access_key=owner_access_key,
                session_name=session_name,
                files=params.files,
            )
        )
        return web.Response(body=result.result, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # download_single (POST /{session_name}/download_single)
    # ------------------------------------------------------------------

    async def download_single(
        self,
        body: BodyParam[DownloadSingleRequest],
        ctx: RequestCtx,
    ) -> web.Response:
        request = ctx.request
        params = body.parsed
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "DOWNLOAD_SINGLE (ak:{0}/{1}, s:{2}, path:{3!r})",
            requester_access_key,
            owner_access_key,
            session_name,
            params.file,
        )
        result = await self._session.download_file.wait_for_complete(
            DownloadFileAction(
                user_id=request["user"]["uuid"],
                session_name=session_name,
                owner_access_key=owner_access_key,
                file=params.file,
            )
        )
        return web.Response(body=result.bytes, status=HTTPStatus.OK)

    # ------------------------------------------------------------------
    # list_files (GET /{session_name}/files)
    # ------------------------------------------------------------------

    async def list_files(
        self,
        query: QueryParam[ListFilesRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = query.parsed
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "LIST_FILES (ak:{0}/{1}, s:{2}, path:{3})",
            requester_access_key,
            owner_access_key,
            session_name,
            params.path,
        )
        result = await self._session.list_files.wait_for_complete(
            ListFilesAction(
                user_id=request["user"]["uuid"],
                path=params.path,
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
        return APIResponse.build(HTTPStatus.OK, ListFilesResponse(dict(result.result)))

    # ------------------------------------------------------------------
    # rename_session (POST /{session_name}/rename)
    # ------------------------------------------------------------------

    async def rename_session(
        self,
        query: QueryParam[RenameSessionRequest],
        ctx: RequestCtx,
    ) -> web.Response:
        request = ctx.request
        params = query.parsed
        session_name = request.match_info["session_name"]
        new_name = params.session_name
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "RENAME_SESSION (ak:{0}/{1}, s:{2}, newname:{3})",
            requester_access_key,
            owner_access_key,
            session_name,
            new_name,
        )
        await self._session.rename_session.wait_for_complete(
            RenameSessionAction(
                session_name=session_name,
                new_name=new_name,
                owner_access_key=owner_access_key,
            )
        )
        return web.Response(status=HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # commit_session (POST /{session_name}/commit)
    # ------------------------------------------------------------------

    async def commit_session(
        self,
        query: QueryParam[CommitSessionRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = query.parsed
        session_name: str = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "COMMIT_SESSION (ak:{}/{}, s:{})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        action_result = await self._session.commit_session.wait_for_complete(
            CommitSessionAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                filename=params.filename,
            )
        )
        return APIResponse.build(
            HTTPStatus.CREATED,
            CommitSessionResponse(dict(action_result.commit_result)),
        )

    # ------------------------------------------------------------------
    # convert_session_to_image (POST /{session_name}/imagify)
    # ------------------------------------------------------------------

    async def convert_session_to_image(
        self,
        query: QueryParam[ConvertSessionToImageRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = query.parsed
        session_name: str = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "CONVERT_SESSION_TO_IMAGE (ak:{}/{}, s:{})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        result = await self._session.convert_session_to_image.wait_for_complete(
            ConvertSessionToImageAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
                image_name=params.image_name,
                image_visibility=params.image_visibility,
                image_owner_id=request["user"]["uuid"],
                user_email=request["user"]["email"],
                max_customized_image_count=request["user"]["resource_policy"][
                    "max_customized_image_count"
                ],
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            ConvertSessionToImageResponse(task_id=str(result.task_id)),
        )

    # ------------------------------------------------------------------
    # get_commit_status (GET /{session_name}/commit)
    # ------------------------------------------------------------------

    async def get_commit_status(
        self,
        query: QueryParam[GetCommitStatusRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        session_name: str = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        myself = asyncio.current_task()
        if myself is None:
            raise NoCurrentTaskContext("No current task context")
        log.info(
            "GET_COMMIT_STATUS (ak:{}/{}, s:{})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        result = await self._session.get_commit_status.wait_for_complete(
            GetCommitStatusAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            GetCommitStatusResponse(result.commit_info.asdict()),
        )

    # ------------------------------------------------------------------
    # get_abusing_report (GET /{session_name}/abusing-report)
    # ------------------------------------------------------------------

    async def get_abusing_report(
        self,
        query: QueryParam[GetAbusingReportRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        session_name: str = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "GET_ABUSING_REPORT (ak:{}/{}, s:{})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        result = await self._session.get_abusing_report.wait_for_complete(
            GetAbusingReportAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            GetAbusingReportResponse(
                cast(dict[str, Any], result.abuse_report) if result.abuse_report else {}
            ),
        )

    # ------------------------------------------------------------------
    # get_status_history (GET /{session_name}/status-history)
    # ------------------------------------------------------------------

    async def get_status_history(
        self,
        query: QueryParam[GetStatusHistoryRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = query.parsed
        session_name: str = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=params.owner_access_key,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "GET_STATUS_HISTORY (ak:{}/{}, s:{})",
            requester_access_key,
            owner_access_key,
            session_name,
        )
        result = await self._session.get_status_history.wait_for_complete(
            GetStatusHistoryAction(
                session_name=session_name,
                owner_access_key=request["keypair"]["access_key"],
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            GetStatusHistoryResponse(result.status_history),
        )

    # ------------------------------------------------------------------
    # get_direct_access_info (GET /{session_name}/direct-access-info)
    # ------------------------------------------------------------------

    async def get_direct_access_info(self, ctx: RequestCtx) -> APIResponse:
        request = ctx.request
        session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        owner_access_key = scope.owner_access_key
        result = await self._session.get_direct_access_info.wait_for_complete(
            GetDirectAccessInfoAction(
                session_name=session_name,
                owner_access_key=owner_access_key,
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            GetDirectAccessInfoResponse(result.result),
        )

    # ------------------------------------------------------------------
    # get_container_logs (GET /{session_name}/logs)
    # ------------------------------------------------------------------

    async def get_container_logs(
        self,
        query: QueryParam[GetContainerLogsRequest],
        ctx: RequestCtx,
    ) -> APIResponse:
        request = ctx.request
        params = query.parsed
        session_name: str = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=params.owner_access_key,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        kernel_id = KernelId(params.kernel_id) if params.kernel_id is not None else None
        log.info(
            "GET_CONTAINER_LOG (ak:{}/{}, s:{}, k:{})",
            requester_access_key,
            owner_access_key,
            session_name,
            kernel_id,
        )
        try:
            result = await self._session.get_container_logs.wait_for_complete(
                GetContainerLogsAction(
                    session_name=session_name,
                    owner_access_key=owner_access_key,
                    kernel_id=kernel_id,
                )
            )
        except BackendAIError:
            log.exception(
                "GET_CONTAINER_LOG(ak:{}/{}, kernel_id: {}, s:{}): unexpected error",
                requester_access_key,
                owner_access_key,
                kernel_id,
                session_name,
            )
            raise
        return APIResponse.build(
            HTTPStatus.OK,
            GetContainerLogsResponse(result.result),
        )

    # ------------------------------------------------------------------
    # get_task_logs (HEAD/GET /_/logs)
    # ------------------------------------------------------------------

    async def get_task_logs(
        self,
        query: QueryParam[GetTaskLogsRequest],
        ctx: RequestCtx,
    ) -> web.StreamResponse:
        request = ctx.request
        params = query.parsed
        log.info(
            "GET_TASK_LOG (ak:{}, k:{})",
            request["keypair"]["access_key"],
            params.kernel_id,
        )
        domain_name = request["user"]["domain_name"]
        user_role = request["user"]["role"]
        user_uuid = request["user"]["uuid"]

        result = await self._vfolder.get_task_logs.wait_for_complete(
            GetTaskLogsAction(
                user_id=user_uuid,
                domain_name=domain_name,
                user_role=user_role,
                kernel_id=KernelId(params.kernel_id),
                owner_access_key=request["keypair"]["access_key"],
                request=request,
            )
        )
        return cast(web.StreamResponse, result.response)

    # ------------------------------------------------------------------
    # get_dependency_graph (GET /{session_name}/dependency-graph)
    # ------------------------------------------------------------------

    async def get_dependency_graph(self, ctx: RequestCtx) -> APIResponse:
        request = ctx.request
        root_session_name = request.match_info["session_name"]
        scope = await self._auth.resolve_access_key_scope.wait_for_complete(
            ResolveAccessKeyScopeAction(
                requester_access_key=request["keypair"]["access_key"],
                requester_role=request["user"]["role"],
                requester_domain=request["user"]["domain_name"],
                owner_access_key=None,
            )
        )
        requester_access_key, owner_access_key = scope.requester_access_key, scope.owner_access_key
        log.info(
            "GET_DEPENDENCY_GRAPH (ak:{0}/{1}, s:{2})",
            requester_access_key,
            owner_access_key,
            root_session_name,
        )
        result = await self._session.get_dependency_graph.wait_for_complete(
            GetDependencyGraphAction(
                root_session_name=root_session_name,
                owner_access_key=owner_access_key,
            )
        )
        return APIResponse.build(
            HTTPStatus.OK,
            GetDependencyGraphResponse(result.result),
        )
