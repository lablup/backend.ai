from __future__ import annotations

import functools
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING, Any, Final

import sqlalchemy as sa
from sqlalchemy.engine import URL
from sqlalchemy.engine import create_engine as _create_engine

from ai.backend.common.exception import DatabaseError
from ai.backend.common.json import ExtendedJSONEncoder
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    from ai.backend.manager.config.bootstrap import BootstrapConfig
    from ai.backend.manager.config.unified import DatabaseConfig

log = StructuredLogger(logging.getLogger(__spec__.name))

TARGET_SESSION_ATTRS_READ_WRITE: Final = "read-write"


def create_async_engine(
    *args: Any,
    _txn_concurrency_threshold: int = 0,
    _lock_conn_timeout: int = 0,
    **kwargs: Any,
) -> ExtendedAsyncSAEngine:
    kwargs["future"] = True
    sync_engine = _create_engine(*args, **kwargs)
    return ExtendedAsyncSAEngine(
        sync_engine,
        _txn_concurrency_threshold=_txn_concurrency_threshold,
        _lock_conn_timeout=_lock_conn_timeout,
    )


def build_db_url(db_config: DatabaseConfig) -> URL:
    """
    URL for create_async_engine(). Lists every primary candidate so asyncpg picks the
    one that accepts writes.
    """
    return URL.create(
        "postgresql+asyncpg",
        username=db_config.user,
        password=db_config.password,
        database=db_config.name,
        query={
            "host": [f"{addr.host}:{addr.port}" for addr in db_config.primary_addrs],
            "target_session_attrs": TARGET_SESSION_ATTRS_READ_WRITE,
        },
    )


def build_libpq_uri(db_config: DatabaseConfig) -> str:
    """
    Connection string for psql (dbshell). Same addresses as build_db_url() in libpq's
    comma-separated form.
    """
    hosts = ",".join(f"{addr.host}:{addr.port}" for addr in db_config.primary_addrs)
    auth = db_config.user
    if db_config.password is not None:
        auth = f"{auth}:{db_config.password}"
    return (
        f"postgres://{auth}@{hosts}/{db_config.name}"
        f"?target_session_attrs={TARGET_SESSION_ATTRS_READ_WRITE}"
    )


@actxmgr
async def connect_database(
    db_config: DatabaseConfig,
    isolation_level: str = "SERIALIZABLE",
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    db_url = build_db_url(db_config)

    version_check_db = create_async_engine(db_url)
    async with version_check_db.begin() as conn:
        result = await conn.execute(sa.text("show server_version"))
        version_str = result.scalar()
        if version_str is None:
            raise DatabaseError("Failed to retrieve PostgreSQL server version")
        major, minor, *_ = map(int, version_str.partition(" ")[0].split("."))
        if (major, minor) < (11, 0):
            pgsql_connect_opts["server_settings"].pop("jit")
    await version_check_db.dispose()

    db = create_async_engine(
        db_url,
        connect_args=pgsql_connect_opts,
        pool_size=db_config.pool_size,
        pool_recycle=db_config.pool_recycle,
        pool_pre_ping=db_config.pool_pre_ping,
        max_overflow=db_config.max_overflow,
        json_serializer=functools.partial(json.dumps, cls=ExtendedJSONEncoder),
        isolation_level=isolation_level,
        future=True,
        _txn_concurrency_threshold=max(
            int(db_config.pool_size + max(0, db_config.max_overflow) * 0.5),
            2,
        ),
        _lock_conn_timeout=int(db_config.lock_conn_timeout),
    )
    yield db
    await db.dispose()


async def vacuum_db(bootstrap_config: BootstrapConfig, vacuum_full: bool = False) -> None:
    async with connect_database(bootstrap_config.db, isolation_level="AUTOCOMMIT") as db:
        async with db.begin() as conn:
            vacuum_sql = "VACUUM FULL" if vacuum_full else "VACUUM"
            log.info("database vacuum started", vacuum_full=vacuum_full)
            await conn.exec_driver_sql(vacuum_sql)
