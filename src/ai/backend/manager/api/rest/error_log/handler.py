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
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.resource import DBOperationFailed
from ai.backend.manager.models.error_logs import error_logs
from ai.backend.manager.models.group import association_groups_users as agus
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.error_log.creators import ErrorLogCreatorSpec
from ai.backend.manager.services.error_log.actions import CreateErrorLogAction
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
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        params = query.parsed

        log.info("LIST (ak:{})", ctx.access_key)
        async with root_ctx.db.begin() as conn:
            is_admin = True
            select_query = (
                sa.select(error_logs)
                .select_from(error_logs)
                .order_by(sa.desc(error_logs.c.created_at))
                .limit(params.page_size)
            )
            count_query = sa.select(sa.func.count()).select_from(error_logs)
            if params.page_no > 1:
                select_query = select_query.offset((params.page_no - 1) * params.page_size)
            if ctx.is_superadmin:
                pass
            elif (
                req.request["user"]["role"] == UserRole.ADMIN
                or req.request["user"]["role"] == "admin"
            ):
                j = groups.join(agus, groups.c.id == agus.c.group_id)
                usr_query = (
                    sa.select(agus.c.user_id)
                    .select_from(j)
                    .where(groups.c.domain_name == ctx.user_domain)
                )
                result = await conn.execute(usr_query)
                usrs = result.fetchall()
                user_ids = [g.user_id for g in usrs]
                where = error_logs.c.user.in_(user_ids)
                select_query = select_query.where(where)
                count_query = count_query.where(where)
            else:
                is_admin = False
                user_where = (error_logs.c.user == ctx.user_uuid) & (~error_logs.c.is_cleared)
                select_query = select_query.where(user_where)
                count_query = count_query.where(user_where)

            result = await conn.execute(select_query)
            log_items: list[ErrorLogDTO] = []
            for row in result:
                user_str = str(row.user) if row.user is not None else None
                log_items.append(
                    ErrorLogDTO(
                        log_id=str(row.id),
                        created_at=datetime.timestamp(row.created_at),
                        severity=row.severity,
                        source=row.source,
                        user=user_str,
                        is_read=row.is_read,
                        message=row.message,
                        context_lang=row.context_lang,
                        context_env=row.context_env,
                        request_url=row.request_url,
                        request_status=row.request_status,
                        traceback=row.traceback,
                        is_cleared=row.is_cleared if is_admin else None,
                    )
                )
            total_count = await conn.scalar(count_query)
            if params.mark_read:
                read_update_query = (
                    sa.update(error_logs)
                    .values(is_read=True)
                    .where(error_logs.c.id.in_([item.log_id for item in log_items]))
                )
                await conn.execute(read_update_query)
            return APIResponse.build(
                HTTPStatus.OK,
                ListErrorLogsResponse(logs=log_items, count=total_count or 0),
            )

    async def mark_cleared(
        self,
        path: PathParam[MarkClearedPathParam],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        path_params = path.parsed
        log_id = uuid.UUID(path_params.log_id)

        log.info("CLEAR")
        async with root_ctx.db.begin() as conn:
            update_query = sa.update(error_logs).values(is_cleared=True)
            if ctx.is_superadmin:
                update_query = update_query.where(error_logs.c.id == log_id)
            elif (
                req.request["user"]["role"] == UserRole.ADMIN
                or req.request["user"]["role"] == "admin"
            ):
                j = groups.join(agus, groups.c.id == agus.c.group_id)
                usr_query = (
                    sa.select(agus.c.user_id)
                    .select_from(j)
                    .where(groups.c.domain_name == ctx.user_domain)
                )
                result = await conn.execute(usr_query)
                usrs = result.fetchall()
                user_ids = [g.user_id for g in usrs]
                update_query = update_query.where(
                    (error_logs.c.user.in_(user_ids)) & (error_logs.c.id == log_id),
                )
            else:
                update_query = update_query.where(
                    (error_logs.c.user == ctx.user_uuid) & (error_logs.c.id == log_id),
                )

            result = await conn.execute(update_query)
            if result.rowcount != 1:
                raise DBOperationFailed(f"Failed to update error log: {log_id}")

            return APIResponse.build(
                HTTPStatus.OK,
                MarkClearedResponse(success=True),
            )
