"""Error log handler class using constructor dependency injection."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, QueryParam
from ai.backend.common.dto.manager.error_log.request import (
    AppendErrorLogRequest,
    ListErrorLogsRequest,
    MarkClearedPathParam,
)
from ai.backend.common.dto.manager.error_log.response import (
    AppendErrorLogResponse,
    ErrorLogDTO,
    ListErrorLogsResponse,
    MarkClearedResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.error_log.creators import ErrorLogCreatorSpec
from ai.backend.manager.services.error_log.actions import CreateErrorLogAction
from ai.backend.manager.services.error_log.actions.list import ListErrorLogsAction
from ai.backend.manager.services.error_log.actions.mark_cleared import MarkClearedErrorLogAction
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ErrorLogHandler:
    """Error log API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    async def append(
        self,
        body: BodyParam[AppendErrorLogRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("CREATE (ak:{})", ctx.access_key)

        severity = ErrorLogSeverity(params.severity.lower())
        creator = Creator(
            spec=ErrorLogCreatorSpec(
                severity=severity,
                source=params.source,
                user=ctx.user_uuid,
                message=params.message,
                context_lang=params.context_lang,
                context_env=params.context_env,
                request_url=params.request_url,
                request_status=params.request_status,
                traceback=params.traceback,
            )
        )
        action = CreateErrorLogAction(creator=creator)
        await self._processors.error_log.create.wait_for_complete(action)

        return APIResponse.build(HTTPStatus.OK, AppendErrorLogResponse(success=True))

    async def list_logs(
        self,
        query: QueryParam[ListErrorLogsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("LIST (ak:{})", ctx.access_key)

        action = ListErrorLogsAction(
            user_uuid=ctx.user_uuid,
            user_domain=ctx.user_domain,
            is_superadmin=ctx.is_superadmin,
            is_admin=ctx.is_admin,
            page_no=params.page_no,
            page_size=params.page_size,
            mark_read=params.mark_read,
        )
        result = await self._processors.error_log.list_logs.wait_for_complete(action)

        is_admin = ctx.is_superadmin or ctx.is_admin
        log_items: list[ErrorLogDTO] = []
        for item in result.logs:
            user_str = str(item.meta.user) if item.meta.user is not None else None
            log_items.append(
                ErrorLogDTO(
                    log_id=str(item.id),
                    created_at=datetime.timestamp(item.meta.created_at),
                    severity=item.content.severity,
                    source=item.meta.source,
                    user=user_str,
                    is_read=item.meta.is_read,
                    message=item.content.message,
                    context_lang=item.meta.context_lang,
                    context_env=item.meta.context_env,
                    request_url=item.meta.request_url,
                    request_status=item.meta.request_status,
                    traceback=item.content.traceback,
                    is_cleared=item.meta.is_cleared if is_admin else None,
                )
            )
        return APIResponse.build(
            HTTPStatus.OK,
            ListErrorLogsResponse(logs=log_items, count=result.total_count),
        )

    async def mark_cleared(
        self,
        path: PathParam[MarkClearedPathParam],
        ctx: UserContext,
    ) -> APIResponse:
        path_params = path.parsed
        log_id = uuid.UUID(path_params.log_id)
        log.info("CLEAR")

        action = MarkClearedErrorLogAction(
            log_id=log_id,
            user_uuid=ctx.user_uuid,
            user_domain=ctx.user_domain,
            is_superadmin=ctx.is_superadmin,
            is_admin=ctx.is_admin,
        )
        await self._processors.error_log.mark_cleared.wait_for_complete(action)

        return APIResponse.build(
            HTTPStatus.OK,
            MarkClearedResponse(success=True),
        )
