from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.error_log import (
    AppendErrorLogRequest,
    AppendErrorLogResponse,
    ListErrorLogsRequest,
    ListErrorLogsResponse,
    MarkClearedResponse,
)


class ErrorLogClient(BaseDomainClient):
    API_PREFIX = "/logs/error"

    async def append(
        self,
        request: AppendErrorLogRequest,
    ) -> AppendErrorLogResponse:
        return await self._client.typed_request(
            "POST",
            self.API_PREFIX,
            request=request,
            response_model=AppendErrorLogResponse,
        )

    async def list_logs(
        self,
        request: ListErrorLogsRequest | None = None,
    ) -> ListErrorLogsResponse:
        params: dict[str, str] | None = None
        if request is not None:
            params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            self.API_PREFIX,
            response_model=ListErrorLogsResponse,
            params=params,
        )

    async def mark_cleared(
        self,
        log_id: uuid.UUID,
    ) -> MarkClearedResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{log_id}/clear",
            response_model=MarkClearedResponse,
        )
