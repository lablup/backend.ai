"""Template database: the schema built once, copied per test.

``CREATE DATABASE ... TEMPLATE`` refuses while anything is connected to the template,
so the engine that built it is disposed before the first clone.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import sqlalchemy as sa

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.models.base import (
    ensure_all_tables_registered,
    metadata,
    pgsql_connect_opts,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.uuid7 import UUID_GENERATE_V7_DDL
from ai.backend.manager.repositories.db.engine import create_async_engine
from ai.backend.testutils.bootstrap import POSTGRES_MAINTENANCE_DB, POSTGRES_PASSWORD, POSTGRES_USER
from bai_scenario import schema as _schema  # the full schema, statically named


def db_url(addr: HostPortPairModel, dbname: str) -> str:
    return (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{addr.host}:{addr.port}/{dbname}"
    )


def engine_for(addr: HostPortPairModel, dbname: str) -> ExtendedAsyncSAEngine:
    return create_async_engine(
        db_url(addr, dbname),
        connect_args=pgsql_connect_opts,
        pool_size=4,
        max_overflow=16,
        pool_pre_ping=False,
    )


async def _admin(addr: HostPortPairModel, *statements: str) -> None:
    engine = create_async_engine(
        db_url(addr, POSTGRES_MAINTENANCE_DB),
        connect_args=pgsql_connect_opts,
        isolation_level="AUTOCOMMIT",
    )
    try:
        async with engine.connect() as conn:
            for statement in statements:
                await conn.execute(sa.text(statement))
    finally:
        await engine.dispose()


async def create_schema(engine: ExtendedAsyncSAEngine) -> None:
    """What ``mgr schema oneshot`` does, minus the alembic stamp."""
    ensure_all_tables_registered()
    assert _schema.registered() > 0
    async with engine.begin() as conn:
        await conn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        await conn.exec_driver_sql(UUID_GENERATE_V7_DDL)
        await conn.run_sync(lambda sync_conn: metadata.create_all(sync_conn, checkfirst=False))


@dataclass(frozen=True)
class TemplateDatabase:
    addr: HostPortPairModel
    name: str
    build_seconds: float


async def create_template(addr: HostPortPairModel, name: str) -> TemplateDatabase:
    started = time.perf_counter()
    await _admin(addr, f'CREATE DATABASE "{name}";')
    engine = engine_for(addr, name)
    try:
        await create_schema(engine)
    finally:
        await engine.dispose()
    return TemplateDatabase(addr, name, time.perf_counter() - started)


async def clone_database(template: TemplateDatabase, name: str) -> float:
    """``CREATE DATABASE name TEMPLATE template``; answers the seconds it took."""
    started = time.perf_counter()
    await _admin(template.addr, f'CREATE DATABASE "{name}" TEMPLATE "{template.name}";')
    return time.perf_counter() - started


async def drop_database(addr: HostPortPairModel, name: str) -> None:
    await _admin(
        addr,
        f'REVOKE CONNECT ON DATABASE "{name}" FROM public;',
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{name}' AND pid <> pg_backend_pid();",
        f'DROP DATABASE "{name}";',
    )
