from __future__ import annotations

import functools
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.engine import create_engine as _create_engine
from yarl import URL

from ai.backend.common.exception import DatabaseError
from ai.backend.common.json import ExtendedJSONEncoder
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    from ai.backend.manager.config.bootstrap import BootstrapConfig
    from ai.backend.manager.config.unified import DatabaseConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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


@actxmgr
async def connect_database(
    db_config: DatabaseConfig,
    isolation_level: str = "SERIALIZABLE",
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    db_url = (
        URL(f"postgresql+asyncpg://{db_config.addr.host}/{db_config.name}")
        .with_port(db_config.addr.port)
        .with_user(db_config.user)
    )
    if db_config.password is not None:
        db_url = db_url.with_password(db_config.password)

    version_check_db = create_async_engine(str(db_url))
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
        str(db_url),
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
            log.info("Performing {} operation...", vacuum_sql)
            await conn.exec_driver_sql(vacuum_sql)
