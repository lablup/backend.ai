from __future__ import annotations

import logging
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING, Any, AsyncIterator

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base

from ai.backend.common.logging import BraceStyleAdapter

from .auth import auth_required
from .manager import ALL_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


Base: Any = declarative_base()


class SessionMetric(Base):
    __tablename__ = "session_computesessionmetric"
    __table_args__ = (sa.PrimaryKeyConstraint("time", "session_id", "status"),)

    time = sa.Column("time", sa.DateTime(timezone=True), index=True, nullable=False)
    session_id = sa.Column("session_id", pgsql.UUID(), nullable=False)
    status = sa.Column("status", sa.String(length=32), nullable=False)
    cpu_util = sa.Column("cpu_util", pgsql.JSONB())
    cpu_used = sa.Column("cpu_used", pgsql.JSONB())
    mem = sa.Column("mem", pgsql.JSONB())
    accel_util = sa.Column("accel_util", pgsql.JSONB())
    accel_mem = sa.Column("accel_mem", pgsql.JSONB())
    io_read = sa.Column("io_read", pgsql.JSONB())
    io_write = sa.Column("io_write", pgsql.JSONB())
    net_rx = sa.Column("net_rx", pgsql.JSONB())
    net_tx = sa.Column("net_tx", pgsql.JSONB())
    accel_type = sa.Column("accel_type", sa.String(length=32))


@actxmgr
async def begin_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        async with AsyncSession(conn) as session:
            async with session.begin():
                yield session


@auth_required
@server_status_required(ALL_ALLOWED)
async def get_user_stat(request: web.Request) -> web.Response:
    root_ctx: RootContext = request.app["_root.context"]
    if root_ctx.stat_db is None:
        # TODO: Add middleware to do null check
        return web.json_response({}, status=200)
    async with begin_session(root_ctx.stat_db) as db_session:
        stmt = sa.select(sa.func.count()).select_from(SessionMetric)
        count = await db_session.scalar(stmt)
        stmt = sa.select(SessionMetric).where(
            SessionMetric.session_id == "35ed3faf-8f09-4d0b-b6cf-f31a2fdf9348"
        )
        res = (await db_session.scalars(stmt)).first()
        print(f"{count = }")
        print(f"{res = }, {res.status = }, {res.time = }")
        return web.json_response({"count": count}, status=200)


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options: CORSOptions) -> tuple[web.Application, list[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "stats"
    app["api_versions"] = (
        4,
        5,
    )
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", get_user_stat))
    return app, []
