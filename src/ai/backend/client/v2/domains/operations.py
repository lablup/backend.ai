from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.operations import (
    AppendErrorLogRequest,
    AppendErrorLogResponse,
    ClearErrorLogResponse,
    FetchManagerStatusResponse,
    GetAnnouncementResponse,
    ListErrorLogsRequest,
    ListErrorLogsResponse,
    PerformSchedulerOpsRequest,
    UpdateAnnouncementRequest,
    UpdateManagerStatusRequest,
)


class OperationsClient(BaseDomainClient):
    """Client for operational endpoints: logs, manager, and scheduler.

    Note: Events endpoints (session events, background task events) use SSE
    streaming and are not supported by this client. They require a dedicated
    streaming mechanism.
    """

    # --- Logs ---

    async def append_error_log(
        self,
        request: AppendErrorLogRequest,
    ) -> AppendErrorLogResponse:
        return await self._client.typed_request(
            "POST",
            "/logs/error",
            request=request,
            response_model=AppendErrorLogResponse,
        )

    async def list_error_logs(
        self,
        request: ListErrorLogsRequest | None = None,
    ) -> ListErrorLogsResponse:
        params: dict[str, str] | None = None
        if request is not None:
            params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/logs/error",
            response_model=ListErrorLogsResponse,
            params=params,
        )

    async def clear_error_log(
        self,
        log_id: str,
    ) -> ClearErrorLogResponse:
        return await self._client.typed_request(
            "POST",
            f"/logs/error/{log_id}/clear",
            response_model=ClearErrorLogResponse,
        )

    # --- Manager ---

    async def get_manager_status(self) -> FetchManagerStatusResponse:
        return await self._client.typed_request(
            "GET",
            "/manager/status",
            response_model=FetchManagerStatusResponse,
        )

    async def update_manager_status(
        self,
        request: UpdateManagerStatusRequest,
    ) -> None:
        await self._client.typed_request_no_content(
            "PUT",
            "/manager/status",
            request=request,
        )

    async def get_announcement(self) -> GetAnnouncementResponse:
        return await self._client.typed_request(
            "GET",
            "/manager/announcement",
            response_model=GetAnnouncementResponse,
        )

    async def update_announcement(
        self,
        request: UpdateAnnouncementRequest,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            "/manager/announcement",
            request=request,
        )

    # --- Scheduler ---

    async def perform_scheduler_ops(
        self,
        request: PerformSchedulerOpsRequest,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            "/manager/scheduler/operation",
            request=request,
        )
