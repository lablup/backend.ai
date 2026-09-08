"""
Per-process test database on the ``postgres_container`` server.

Every pytest process gets its own ``test_db_<token>`` database, so several processes
can share one PostgreSQL server while ``with_tables`` creates and truncates tables.
Register with ``pytest_plugins = ["ai.backend.testutils.db_fixtures"]``.
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator, Iterator

import pytest
import sqlalchemy as sa

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.db.engine import create_async_engine
from ai.backend.testutils.bootstrap import (
    POSTGRES_MAINTENANCE_DB,
    POSTGRES_PASSWORD,
    POSTGRES_USER,
)


def _url(addr: HostPortPairModel, dbname: str) -> str:
    return (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{addr.host}:{addr.port}/{dbname}"
    )


async def _create_database(addr: HostPortPairModel, dbname: str) -> None:
    engine = create_async_engine(
        _url(addr, POSTGRES_MAINTENANCE_DB),
        connect_args=pgsql_connect_opts,
        isolation_level="AUTOCOMMIT",
    )
    try:
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(sa.text(f'CREATE DATABASE "{dbname}";'))
            except (ConnectionError, OSError):
                await asyncio.sleep(0.1)
                continue
            break
    finally:
        await engine.dispose()


async def _drop_database(addr: HostPortPairModel, dbname: str) -> None:
    engine = create_async_engine(
        _url(addr, POSTGRES_MAINTENANCE_DB),
        connect_args=pgsql_connect_opts,
        isolation_level="AUTOCOMMIT",
    )
    try:
        async with engine.connect() as conn:
            await conn.execute(sa.text(f'REVOKE CONNECT ON DATABASE "{dbname}" FROM public;'))
            await conn.execute(
                sa.text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    f"WHERE datname = '{dbname}' AND pid <> pg_backend_pid();"
                )
            )
            await conn.execute(sa.text(f'DROP DATABASE "{dbname}";'))
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def test_database_url(
    postgres_container: tuple[str, HostPortPairModel],
) -> Iterator[str]:
    _, addr = postgres_container
    dbname = f"test_db_{secrets.token_hex(12)}"
    asyncio.run(_create_database(addr, dbname))
    yield _url(addr, dbname)
    asyncio.run(_drop_database(addr, dbname))


@pytest.fixture
async def database_connection(test_database_url: str) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """
    Engine on the per-process database, no tables created.
    Use with ``with_tables`` from ``ai.backend.testutils.db``.
    Function-scoped so each test's event loop owns its asyncpg connections.
    """
    engine = create_async_engine(
        test_database_url,
        pool_size=8,
        pool_pre_ping=False,
        max_overflow=64,
    )
    yield engine
    await engine.dispose()
