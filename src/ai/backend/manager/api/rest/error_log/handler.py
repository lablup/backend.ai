"""Error log handler class using constructor dependency injection."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Final

import sqlalchemy as sa

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
from ai.backend.common.identifier.user import UserID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.models.error_log.creators import ErrorLogCreator
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.error_log.searchers import ErrorLogSearcher
from ai.backend.manager.services.error_log.actions import CreateErrorLogAction
from ai.backend.manager.services.error_log.actions.admin_search import AdminSearchErrorLogsAction
from ai.backend.manager.services.error_log.actions.delete import DeleteErrorLogAction
from ai.backend.manager.services.error_log.actions.search import SearchErrorLogsAction
from ai.backend.manager.services.error_log.processors import ErrorLogProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ErrorLogHandler:
    """Error log API handler with constructor-injected dependencies."""

    def __init__(self, *, error_log: ErrorLogProcessors) -> None:
        self._error_log = error_log

    async def append(
        self,
        body: BodyParam[AppendErrorLogRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = body.parsed
        log.info("CREATE (ak:{})", ctx.access_key)

        severity = ErrorLogSeverity(params.severity.lower())
        creator = ErrorLogCreator(
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
        action = CreateErrorLogAction(user_id=UserID(ctx.user_uuid), creator=creator)
        await self._error_log.create.run(action)

        return APIResponse.build(HTTPStatus.OK, AppendErrorLogResponse(success=True))

    async def list_logs(
        self,
        query: QueryParam[ListErrorLogsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info("LIST (ak:{})", ctx.access_key)

        searcher = ErrorLogSearcher(
            pagination=OffsetPagination(
                limit=params.page_size,
                offset=(params.page_no - 1) * params.page_size,
            ),
            orders=[sa.desc(ErrorLogRow.created_at)],
        )
        # A super admin reads the whole table through the global action; everyone else
        # reads within their own scope. The branch lives here because the two are
        # separate actions with separate gates, not one action that widens itself.
        if ctx.is_superadmin:
            result = await self._error_log.search.run(AdminSearchErrorLogsAction(searcher=searcher))
        else:
            result = await self._error_log.scoped_search.run(
                SearchErrorLogsAction(user_id=UserID(ctx.user_uuid), searcher=searcher)
            )

        is_admin = ctx.is_superadmin or ctx.is_admin
        log_items: list[ErrorLogDTO] = []
        for item in result.items:
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

        action = DeleteErrorLogAction(log_id=log_id)
        await self._error_log.delete.run(action)

        return APIResponse.build(
            HTTPStatus.OK,
            MarkClearedResponse(success=True),
        )
