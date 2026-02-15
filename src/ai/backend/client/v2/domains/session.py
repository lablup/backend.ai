from __future__ import annotations

from typing import Any

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.session.request import (
    CommitSessionRequest,
    CompleteRequest,
    ConvertSessionToImageRequest,
    CreateClusterRequest,
    CreateFromParamsRequest,
    CreateFromTemplateRequest,
    DestroySessionRequest,
    ExecuteRequest,
    GetAbusingReportRequest,
    GetCommitStatusRequest,
    GetContainerLogsRequest,
    GetStatusHistoryRequest,
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

_BASE_PATH = "/session"


class SessionClient(BaseDomainClient):
    # -----------------------------------------------------------------------
    # Session creation
    # -----------------------------------------------------------------------

    async def create_from_params(
        self,
        request: CreateFromParamsRequest,
    ) -> CreateSessionResponse:
        return await self._client.typed_request(
            "POST",
            _BASE_PATH,
            request=request,
            response_model=CreateSessionResponse,
        )

    async def create_from_template(
        self,
        request: CreateFromTemplateRequest,
    ) -> CreateSessionResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/_/create-from-template",
            request=request,
            response_model=CreateSessionResponse,
        )

    async def create_cluster(
        self,
        request: CreateClusterRequest,
    ) -> CreateSessionResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/_/create-cluster",
            request=request,
            response_model=CreateSessionResponse,
        )

    # -----------------------------------------------------------------------
    # Session lifecycle
    # -----------------------------------------------------------------------

    async def get_info(
        self,
        session_name: str,
        *,
        owner_access_key: str | None = None,
    ) -> GetSessionInfoResponse:
        params = {"owner_access_key": owner_access_key} if owner_access_key else None
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}",
            response_model=GetSessionInfoResponse,
            params=params,
        )

    async def restart(
        self,
        session_name: str,
        request: RestartSessionRequest | None = None,
    ) -> None:
        await self._client.typed_request_no_content(
            "PATCH",
            f"{_BASE_PATH}/{session_name}",
            request=request,
        )

    async def destroy(
        self,
        session_name: str,
        request: DestroySessionRequest | None = None,
    ) -> DestroySessionResponse:
        return await self._client.typed_request(
            "DELETE",
            f"{_BASE_PATH}/{session_name}",
            request=request,
            response_model=DestroySessionResponse,
        )

    async def rename(
        self,
        session_name: str,
        request: RenameSessionRequest,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            f"{_BASE_PATH}/{session_name}/rename",
            request=request,
        )

    async def interrupt(
        self,
        session_name: str,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            f"{_BASE_PATH}/{session_name}/interrupt",
        )

    async def match_sessions(
        self,
        request: MatchSessionsRequest,
    ) -> MatchSessionsResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/_/match",
            request=request,
            response_model=MatchSessionsResponse,
        )

    # -----------------------------------------------------------------------
    # Code execution
    # -----------------------------------------------------------------------

    async def execute(
        self,
        session_name: str,
        request: ExecuteRequest,
    ) -> ExecuteResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/{session_name}",
            request=request,
            response_model=ExecuteResponse,
        )

    async def complete(
        self,
        session_name: str,
        request: CompleteRequest,
    ) -> CompleteResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/{session_name}/complete",
            request=request,
            response_model=CompleteResponse,
        )

    # -----------------------------------------------------------------------
    # Services
    # -----------------------------------------------------------------------

    async def start_service(
        self,
        session_name: str,
        request: StartServiceRequest,
    ) -> StartServiceResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/{session_name}/start-service",
            request=request,
            response_model=StartServiceResponse,
        )

    async def shutdown_service(
        self,
        session_name: str,
        request: ShutdownServiceRequest,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            f"{_BASE_PATH}/{session_name}/shutdown-service",
            request=request,
        )

    # -----------------------------------------------------------------------
    # Commit / imagify
    # -----------------------------------------------------------------------

    async def commit(
        self,
        session_name: str,
        request: CommitSessionRequest,
    ) -> CommitSessionResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/{session_name}/commit",
            request=request,
            response_model=CommitSessionResponse,
        )

    async def get_commit_status(
        self,
        session_name: str,
        request: GetCommitStatusRequest | None = None,
    ) -> GetCommitStatusResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}/commit",
            request=request,
            response_model=GetCommitStatusResponse,
        )

    async def convert_to_image(
        self,
        session_name: str,
        request: ConvertSessionToImageRequest,
    ) -> ConvertSessionToImageResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/{session_name}/imagify",
            request=request,
            response_model=ConvertSessionToImageResponse,
        )

    # -----------------------------------------------------------------------
    # Files & logs
    # -----------------------------------------------------------------------

    async def list_files(
        self,
        session_name: str,
        request: ListFilesRequest | None = None,
    ) -> ListFilesResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}/files",
            request=request,
            response_model=ListFilesResponse,
        )

    async def get_container_logs(
        self,
        session_name: str,
        request: GetContainerLogsRequest | None = None,
    ) -> GetContainerLogsResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}/logs",
            request=request,
            response_model=GetContainerLogsResponse,
        )

    async def get_status_history(
        self,
        session_name: str,
        request: GetStatusHistoryRequest | None = None,
    ) -> GetStatusHistoryResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}/status-history",
            request=request,
            response_model=GetStatusHistoryResponse,
        )

    # -----------------------------------------------------------------------
    # Other
    # -----------------------------------------------------------------------

    async def get_direct_access_info(
        self,
        session_name: str,
    ) -> GetDirectAccessInfoResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}/direct-access-info",
            response_model=GetDirectAccessInfoResponse,
        )

    async def get_dependency_graph(
        self,
        session_name: str,
    ) -> GetDependencyGraphResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}/dependency-graph",
            response_model=GetDependencyGraphResponse,
        )

    async def get_abusing_report(
        self,
        session_name: str,
        request: GetAbusingReportRequest | None = None,
    ) -> GetAbusingReportResponse:
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/{session_name}/abusing-report",
            request=request,
            response_model=GetAbusingReportResponse,
        )

    # -----------------------------------------------------------------------
    # Admin / internal
    # -----------------------------------------------------------------------

    async def sync_agent_registry(
        self,
        request: SyncAgentRegistryRequest,
    ) -> dict[str, Any] | None:
        result: dict[str, Any] | None = await self._client._request(
            "POST",
            f"{_BASE_PATH}/_/sync-agent-registry",
            json=request.model_dump(exclude_none=True),
        )
        return result

    async def transit_session_status(
        self,
        request: TransitSessionStatusRequest,
    ) -> TransitSessionStatusResponse:
        return await self._client.typed_request(
            "POST",
            f"{_BASE_PATH}/_/transit-status",
            request=request,
            response_model=TransitSessionStatusResponse,
        )

    # -----------------------------------------------------------------------
    # Deferred — require binary/multipart/streaming support
    # -----------------------------------------------------------------------
    # TODO: upload_files — POST multipart
    # TODO: download_files — POST, returns ZIP binary
    # TODO: download_single — POST, returns file binary
    # TODO: get_task_logs — GET/HEAD, returns streaming response
