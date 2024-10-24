import asyncio
import functools
import json
import logging
from contextlib import AbstractAsyncContextManager as AbstractAsyncCtxMgr
from contextlib import asynccontextmanager as actxmgr
from typing import (
    AsyncIterator,
    Awaitable,
    Callable,
    Concatenate,
    ParamSpec,
    TypeVar,
    cast,
)
from urllib.parse import quote_plus as urlquote

import sqlalchemy as sa
from sqlalchemy.engine import create_engine as _create_engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import sessionmaker
from tenacity import (
    AsyncRetrying,
    RetryError,
    TryAgain,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ai.backend.common.json import ExtendedJSONEncoder
from ai.backend.common.logging import BraceStyleAdapter

from ..config import ServerConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


def is_db_retry_error(e: Exception) -> bool:
    return isinstance(e, DBAPIError) and getattr(e.orig, "pgcode", None) == "40001"


P = ParamSpec("P")
TQueryResult = TypeVar("TQueryResult")


class ExtendedAsyncSAEngine(SAEngine):
    """
    A subclass to add a few more convenience methods to the SQLAlchemy's async engine.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._txn_concurrency_threshold = kwargs.pop("_txn_concurrency_threshold", 0)
        super().__init__(*args, **kwargs)
        self._readonly_txn_count = 0
        self._generic_txn_count = 0
        self._sess_factory = sessionmaker(self, expire_on_commit=False, class_=SASession)
        self._readonly_sess_factory = sessionmaker(self, class_=SASession)

    def _check_generic_txn_cnt(self) -> None:
        if (
            self._txn_concurrency_threshold > 0
            and self._generic_txn_count >= self._txn_concurrency_threshold
        ):
            log.warning(
                "The number of concurrent generic transactions ({}) "
                "looks too high (warning threshold: {}).",
                self._generic_txn_count,
                self._txn_concurrency_threshold,
                stack_info=False,
            )

    def _check_readonly_txn_cnt(self) -> None:
        if (
            self._txn_concurrency_threshold > 0
            and self._readonly_txn_count >= self._txn_concurrency_threshold
        ):
            log.warning(
                "The number of concurrent read-only transactions ({}) "
                "looks too high (warning threshold: {}).",
                self._readonly_txn_count,
                self._txn_concurrency_threshold,
                stack_info=False,
            )

    @actxmgr
    async def _begin(self, connection: SAConnection) -> AsyncIterator[SAConnection]:
        """
        Begin generic transaction within the given connection.
        """
        async with connection.begin():
            self._generic_txn_count += 1
            self._check_generic_txn_cnt()
            try:
                yield connection
            finally:
                self._generic_txn_count -= 1

    @actxmgr
    async def _begin_readonly(
        self, connection: SAConnection, deferrable: bool = False
    ) -> AsyncIterator[SAConnection]:
        """
        Begin read-only transaction within the given connection.
        """
        conn_with_exec_opts = await connection.execution_options(
            postgresql_readonly=True,
            postgresql_deferrable=deferrable,
        )
        async with conn_with_exec_opts.begin():
            self._readonly_txn_count += 1
            self._check_readonly_txn_cnt()
            try:
                yield conn_with_exec_opts
            finally:
                self._readonly_txn_count -= 1

    @actxmgr
    async def begin_session(
        self,
        bind: SAConnection | None = None,
        expire_on_commit: bool = False,
        commit_on_end: bool = True,
    ) -> AsyncIterator[SASession]:
        @actxmgr
        async def _begin_session(connection: SAConnection) -> AsyncIterator[SASession]:
            async with self._begin(connection) as conn:
                self._sess_factory.configure(bind=conn, expire_on_commit=expire_on_commit)
                session = self._sess_factory()
                yield session
                if commit_on_end:
                    await session.commit()

        if bind is None:
            async with self.connect() as _bind:
                async with _begin_session(_bind) as sess:
                    yield sess
        else:
            async with _begin_session(bind) as sess:
                yield sess

    @actxmgr
    async def begin_readonly_session(
        self,
        bind: SAConnection | None = None,
        deferrable: bool = False,
    ) -> AsyncIterator[SASession]:
        @actxmgr
        async def _begin_session(connection: SAConnection) -> AsyncIterator[SASession]:
            async with self._begin_readonly(connection, deferrable) as conn:
                self._readonly_sess_factory.configure(bind=conn)
                session = self._readonly_sess_factory()
                yield session

        if bind is None:
            async with self.connect() as _conn:
                async with _begin_session(_conn) as sess:
                    yield sess
        else:
            async with _begin_session(bind) as sess:
                yield sess

    async def execute_with_txn_retry(
        self,
        txn_func: Callable[Concatenate[SASession, P], Awaitable[TQueryResult]],
        connection: SAConnection,
        begin_trx: Callable[..., AbstractAsyncCtxMgr[SASession]] | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> TQueryResult:
        """
        Execute DB related function by retrying transaction in a given connection.

        The transaction retry resolves Postgres's Serialization error.
        Reference: https://www.postgresql.org/docs/current/mvcc-serialization-failure-handling.html
        """

        # result: TQueryResult | Sentinel = Sentinel.token
        _begin_trx = cast(
            Callable[..., AbstractAsyncCtxMgr[SASession]],
            self.begin_session if begin_trx is None else begin_trx,
        )

        max_attempts = 10
        try:
            async for attempt in AsyncRetrying(
                wait=wait_exponential(multiplier=0.02, min=0.02, max=1.0),
                stop=stop_after_attempt(max_attempts),
                retry=retry_if_exception_type(TryAgain),
            ):
                with attempt:
                    try:
                        async with _begin_trx(bind=connection) as session_or_conn:
                            result = await txn_func(session_or_conn, *args, **kwargs)
                    except DBAPIError as e:
                        if is_db_retry_error(e):
                            raise TryAgain
                        raise
        except RetryError:
            raise asyncio.TimeoutError(
                f"DB serialization failed after {max_attempts} retry transactions"
            )
        return result


def create_async_engine(
    *args,
    _txn_concurrency_threshold: int = 0,
    **kwargs,
) -> ExtendedAsyncSAEngine:
    kwargs["future"] = True
    sync_engine = _create_engine(*args, **kwargs)
    return ExtendedAsyncSAEngine(
        sync_engine,
        _txn_concurrency_threshold=_txn_concurrency_threshold,
    )


@actxmgr
async def connect_database(
    local_config: ServerConfig,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    from .base import pgsql_connect_opts

    username = local_config.db.user
    password = local_config.db.password
    address = local_config.db.addr
    dbname = local_config.db.name
    url = f"postgresql+asyncpg://{urlquote(username)}:{urlquote(password)}@{address}/{urlquote(dbname)}"

    version_check_db = create_async_engine(url)
    async with version_check_db.begin() as conn:
        result = await conn.execute(sa.text("show server_version"))
        version_str = result.scalar()
        major, minor, *_ = map(int, version_str.partition(" ")[0].split("."))
        if (major, minor) < (11, 0):
            pgsql_connect_opts["server_settings"].pop("jit")
    await version_check_db.dispose()

    db = create_async_engine(
        url,
        connect_args=pgsql_connect_opts,
        pool_size=local_config.db.pool_size,
        pool_recycle=local_config.db.pool_recycle,
        pool_pre_ping=local_config.db.pool_pre_ping,
        max_overflow=local_config.db.max_overflow,
        json_serializer=functools.partial(json.dumps, cls=ExtendedJSONEncoder),
        isolation_level=local_config.db.transaction_isolation,
        future=True,
        _txn_concurrency_threshold=max(
            int(local_config.db.pool_size + max(0, local_config.db.max_overflow) * 0.5),
            2,
        ),
    )
    yield db
    await db.dispose()
