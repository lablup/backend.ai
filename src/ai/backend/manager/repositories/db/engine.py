from __future__ import annotations

import functools
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING, Any

import asyncpg
import sqlalchemy as sa
from sqlalchemy.engine import create_engine as _create_engine

from ai.backend.common.exception import DatabaseError
from ai.backend.common.json import ExtendedJSONEncoder
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    from ai.backend.common.typed_validators import HostPortPair
    from ai.backend.manager.config.bootstrap import BootstrapConfig
    from ai.backend.manager.config.unified import DatabaseConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def create_async_engine(
    *args: Any,
    _txn_concurrency_threshold: int = 0,
    _lock_conn_timeout: int = 0,
    async_creator: Callable[[], Awaitable[asyncpg.Connection]] | None = None,
    **kwargs: Any,
) -> ExtendedAsyncSAEngine:
    kwargs["future"] = True
    sync_engine: sa.engine.Engine
    if async_creator is not None:
        # Same adaptation as sqlalchemy.ext.asyncio.create_async_engine(async_creator=...)
        kwargs["creator"] = lambda: sync_engine.dialect.loaded_dbapi.connect(
            async_creator_fn=async_creator
        )
    sync_engine = _create_engine(*args, **kwargs)
    return ExtendedAsyncSAEngine(
        sync_engine,
        _txn_concurrency_threshold=_txn_concurrency_threshold,
        _lock_conn_timeout=_lock_conn_timeout,
    )


class PrimaryMemberConnector:
    """
    Connects to the first member of a PostgreSQL cluster that is not in hot standby,
    starting from the member that answered as the primary last time.
    """

    _members: list[HostPortPair]
    _connect_timeout: float
    _connect_kwargs: dict[str, Any]
    _start: int

    def __init__(self, db_config: DatabaseConfig, connect_kwargs: dict[str, Any]) -> None:
        self._members = db_config.addrs
        self._connect_timeout = db_config.connect_timeout
        self._connect_kwargs = {
            **connect_kwargs,
            "user": db_config.user,
            "password": db_config.password,
            "database": db_config.name,
        }
        self._start = 0

    async def connect(self) -> asyncpg.Connection:
        last_error: Exception | None = None
        count = len(self._members)
        for index in [(self._start + offset) % count for offset in range(count)]:
            member = self._members[index]
            try:
                conn = await asyncpg.connect(
                    host=member.host,
                    port=member.port,
                    timeout=self._connect_timeout,
                    **self._connect_kwargs,
                )
            except (OSError, asyncpg.PostgresError) as e:
                log.warning(
                    "database member connection failed", addr=str(member), failure_reason=repr(e)
                )
                last_error = e
                continue
            try:
                in_hot_standby = await self._in_hot_standby(conn)
            except (OSError, asyncpg.PostgresError) as e:
                conn.terminate()
                log.warning(
                    "database member connection failed", addr=str(member), failure_reason=repr(e)
                )
                last_error = e
                continue
            except BaseException:
                conn.terminate()
                raise
            if not in_hot_standby:
                self._start = index
                return conn
            conn.terminate()
        if last_error is not None:
            raise last_error
        raise asyncpg.TargetServerAttributeNotMatched("None of the cluster members is a primary")

    async def _in_hot_standby(self, conn: asyncpg.Connection) -> bool:
        # PostgreSQL 14+ reports in_hot_standby at startup.
        reported: str | None = getattr(conn.get_settings(), "in_hot_standby", None)
        if reported is not None:
            return reported == "on"
        return bool(
            await conn.fetchval(
                "SELECT pg_catalog.pg_is_in_recovery()", timeout=self._connect_timeout
            )
        )


@actxmgr
async def connect_database(
    db_config: DatabaseConfig,
    isolation_level: str = "SERIALIZABLE",
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    db_url = db_config.sqlalchemy_url()

    version_check_db = create_async_engine(
        db_url, async_creator=PrimaryMemberConnector(db_config, {}).connect
    )
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
        async_creator=PrimaryMemberConnector(db_config, pgsql_connect_opts).connect,
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
