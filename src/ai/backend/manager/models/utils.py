from __future__ import annotations

import asyncio
import functools
import json
import logging
from contextlib import AbstractAsyncContextManager as AbstractAsyncCtxMgr
from contextlib import asynccontextmanager as actxmgr
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Concatenate,
    Mapping,
    ParamSpec,
    Tuple,
    TypeAlias,
    TypeVar,
    overload,
)
from urllib.parse import quote_plus as urlquote

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql
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

if TYPE_CHECKING:
    from ..config import LocalConfig

from ..defs import LockID
from ..types import Sentinel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
column_constraints = ["nullable", "index", "unique", "primary_key"]

# TODO: Implement begin(), begin_readonly() for AsyncSession also


class ExtendedAsyncSAEngine(SAEngine):
    """
    A subclass to add a few more convenience methods to the SQLAlchemy's async engine.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._txn_concurrency_threshold = kwargs.pop("_txn_concurrency_threshold", 0)
        self.lock_conn_timeout: float | None = (
            kwargs.pop("_lock_conn_timeout", 0) or None
        )  # Convert 0 to `None`
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
    async def begin(self, bind: SAConnection | None = None) -> AsyncIterator[SAConnection]:
        if bind is None:
            async with self.connect() as _bind:
                async with self._begin(_bind) as conn:
                    yield conn
        else:
            async with self._begin(bind) as conn:
                yield conn

    @actxmgr
    async def begin_readonly(
        self, bind: SAConnection | None = None, deferrable: bool = False
    ) -> AsyncIterator[SAConnection]:
        if bind is None:
            async with self.connect() as _bind:
                async with self._begin_readonly(_bind, deferrable) as conn:
                    yield conn
        else:
            async with self._begin_readonly(bind, deferrable) as conn:
                yield conn

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

    @actxmgr
    async def advisory_lock(self, lock_id: LockID) -> AsyncIterator[None]:
        lock_acquired = False
        # Here we use the session-level advisory lock,
        # which follows the lifetime of underlying DB connection.
        # As such, we should keep using one single connection for both lock and unlock ops.
        async with self.connect() as lock_conn:
            try:
                # It is usually a BAD practice to directly interpolate strings into SQL statements,
                # but in this case:
                #  - The lock ID is only given from trusted codes.
                #  - asyncpg does not support parameter interpolation with raw SQL statements.
                async with asyncio.timeout(self.lock_conn_timeout):
                    await lock_conn.exec_driver_sql(
                        f"SELECT pg_advisory_lock({lock_id:d});",
                    )
                    lock_acquired = True
                    yield
            except sa.exc.DBAPIError as e:
                if getattr(e.orig, "pgcode", None) == "55P03":  # lock not available error
                    # This may happen upon shutdown after some time.
                    raise asyncio.CancelledError()
                raise
            except asyncio.CancelledError:
                raise
            finally:
                if lock_acquired and not lock_conn.closed:
                    try:
                        await lock_conn.exec_driver_sql(
                            f"SELECT pg_advisory_unlock({lock_id:d})",
                        )
                    except sa.exc.InterfaceError:
                        log.warning(
                            f"DB Connnection for lock(id: {lock_id:d}) has already been closed. Skip unlock"
                        )


P = ParamSpec("P")
TQueryResult = TypeVar("TQueryResult")


@overload
async def execute_with_txn_retry(
    txn_func: Callable[Concatenate[SASession, P], Awaitable[TQueryResult]],
    begin_trx: Callable[..., AbstractAsyncCtxMgr[SASession]],
    connection: SAConnection,
    *args: P.args,
    **kwargs: P.kwargs,
) -> TQueryResult: ...


# Setting "type ignore" here becuase Mypy deduces all fields and attributes in `sqlalchemy` module to `Any` type
# including `SASession` and `SAConnection`.
@overload
async def execute_with_txn_retry(  # type: ignore[misc]
    txn_func: Callable[Concatenate[SAConnection, P], Awaitable[TQueryResult]],
    begin_trx: Callable[..., AbstractAsyncCtxMgr[SAConnection]],
    connection: SAConnection,
    *args: P.args,
    **kwargs: P.kwargs,
) -> TQueryResult: ...


# TODO: Allow `SASession` parameter only, remove type overloading and remove `begin_trx` after migrating Core APIs to ORM APIs.
async def execute_with_txn_retry(
    txn_func: Callable[Concatenate[SASession, P], Awaitable[TQueryResult]]
    | Callable[Concatenate[SAConnection, P], Awaitable[TQueryResult]],
    begin_trx: Callable[..., AbstractAsyncCtxMgr[SASession]]
    | Callable[..., AbstractAsyncCtxMgr[SAConnection]],
    connection: SAConnection,
    *args: P.args,
    **kwargs: P.kwargs,
) -> TQueryResult:
    """
    Execute DB related function by retrying transaction in a given connection.

    The transaction retry resolves Postgres's Serialization error.
    Reference: https://www.postgresql.org/docs/current/mvcc-serialization-failure-handling.html
    """

    result: TQueryResult | Sentinel = Sentinel.token
    max_attempts = 10
    try:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=0.02, min=0.02, max=1.0),
            stop=stop_after_attempt(max_attempts),
            retry=retry_if_exception_type(TryAgain),
        ):
            with attempt:
                try:
                    async with begin_trx(bind=connection) as session_or_conn:
                        result = await txn_func(session_or_conn, *args, **kwargs)
                except DBAPIError as e:
                    if is_db_retry_error(e):
                        raise TryAgain
                    raise
    except RetryError:
        raise asyncio.TimeoutError(
            f"DB serialization failed after {max_attempts} retry transactions"
        )
    assert result is not Sentinel.token
    return result


def create_async_engine(
    *args,
    _txn_concurrency_threshold: int = 0,
    _lock_conn_timeout: int = 0,
    **kwargs,
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
    local_config: LocalConfig | Mapping[str, Any],
    isolation_level: str = "SERIALIZABLE",
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    from .base import pgsql_connect_opts

    username = local_config["db"]["user"]
    password = local_config["db"]["password"]
    address = local_config["db"]["addr"]
    dbname = local_config["db"]["name"]
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
        pool_size=local_config["db"]["pool-size"],
        pool_recycle=local_config["db"]["pool-recycle"],
        pool_pre_ping=local_config["db"]["pool-pre-ping"],
        max_overflow=local_config["db"]["max-overflow"],
        json_serializer=functools.partial(json.dumps, cls=ExtendedJSONEncoder),
        isolation_level=isolation_level,
        future=True,
        _txn_concurrency_threshold=max(
            int(local_config["db"]["pool-size"] + max(0, local_config["db"]["max-overflow"]) * 0.5),
            2,
        ),
        _lock_conn_timeout=local_config["db"]["lock-conn-timeout"],
    )
    yield db
    await db.dispose()


@actxmgr
async def reenter_txn(
    pool: ExtendedAsyncSAEngine,
    conn: SAConnection,
    execution_opts: Mapping[str, Any] | None = None,
) -> AsyncIterator[SAConnection]:
    if conn is None:
        async with pool.connect() as conn:
            if execution_opts:
                await conn.execution_options(**execution_opts)
            async with conn.begin():
                yield conn
    else:
        async with conn.begin_nested():
            yield conn


@actxmgr
async def reenter_txn_session(
    pool: ExtendedAsyncSAEngine,
    sess: SASession,
    read_only: bool = False,
) -> AsyncIterator[SAConnection]:
    if sess is None:
        if read_only:
            async with pool.begin_readonly_session() as sess:
                yield sess
        else:
            async with pool.begin_session() as sess:
                yield sess
    else:
        async with sess.begin_nested():
            yield sess


async def execute_with_retry(txn_func: Callable[[], Awaitable[TQueryResult]]) -> TQueryResult:
    max_attempts = 20
    result: TQueryResult | Sentinel = Sentinel.token
    try:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=0.02, min=0.02, max=5.0),
            stop=stop_after_attempt(max_attempts),
            retry=retry_if_exception_type(TryAgain),
        ):
            with attempt:
                try:
                    result = await txn_func()
                except DBAPIError as e:
                    if is_db_retry_error(e):
                        raise TryAgain
                    raise
    except RetryError:
        raise RuntimeError(f"DB serialization failed after {max_attempts} retries")
    assert result is not Sentinel.token
    return result


JSONCoalesceExpr: TypeAlias = sa.sql.elements.BinaryExpression


def sql_json_merge(
    col,
    key: Tuple[str, ...],
    obj: Mapping[str, Any],
    *,
    _depth: int = 0,
) -> JSONCoalesceExpr:
    """
    Generate an SQLAlchemy column update expression that merges the given object with
    the existing object at a specific (nested) key of the given JSONB column,
    with automatic creation of empty objects in parents and the target level.

    Note that the existing value must be also an object, not a primitive value.
    """
    expr = sa.func.coalesce(
        col if _depth == 0 else col[key[:_depth]],
        sa.text("'{}'::jsonb"),
    ).concat(
        (
            sa.func.jsonb_build_object(
                key[_depth],
                (
                    sa.func.coalesce(col[key], sa.text("'{}'::jsonb")).concat(
                        sa.func.cast(obj, psql.JSONB)
                    )
                    if _depth == len(key) - 1
                    else sql_json_merge(col, key, obj=obj, _depth=_depth + 1)
                ),
            )
            if key
            else sa.func.cast(obj, psql.JSONB)
        ),
    )
    return expr


def sql_json_increment(
    col,
    key: Tuple[str, ...],
    *,
    parent_updates: Mapping[str, Any] = None,
    _depth: int = 0,
) -> JSONCoalesceExpr:
    """
    Generate an SQLAlchemy column update expression that increments the value at a specific
    (nested) key of the given JSONB column,
    with automatic creation of empty objects in parents and population of the
    optional parent_updates object to the target key's parent.

    Note that the existing value of the parent key must be also an object, not a primitive value.
    """
    expr = sa.func.coalesce(
        col if _depth == 0 else col[key[:_depth]],
        sa.text("'{}'::jsonb"),
    ).concat(
        sa.func.jsonb_build_object(
            key[_depth],
            (
                sa.func.coalesce(col[key].as_integer(), 0) + 1
                if _depth == len(key) - 1
                else sql_json_increment(col, key, parent_updates=parent_updates, _depth=_depth + 1)
            ),
        ),
    )
    if _depth == len(key) - 1 and parent_updates is not None:
        expr = expr.concat(sa.func.cast(parent_updates, psql.JSONB))
    return expr


def _populate_column(column: sa.Column):
    column_attrs = dict(column.__dict__)
    name = column_attrs.pop("name")
    return sa.Column(name, column.type, **{k: column_attrs[k] for k in column_constraints})


def regenerate_table(table: sa.Table, new_metadata: sa.MetaData) -> sa.Table:
    """
    This function can be used to regenerate table which belongs to SQLAlchemy ORM Class,
    which can be helpful when you're tring to build fresh new table for use on diffrent context
    than main manager logic (e.g. test code).
    Check out tests/test_image.py for more details.
    """
    return sa.Table(
        table.name,
        new_metadata,
        *[_populate_column(c) for c in table.columns],
    )


def agg_to_str(column: sa.Column) -> sa.sql.functions.Function:
    # https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#sqlalchemy.dialects.postgresql.aggregate_order_by
    return sa.func.string_agg(column, psql.aggregate_order_by(sa.literal_column("','"), column))


def agg_to_array(column: sa.Column) -> sa.sql.functions.Function:
    return sa.func.array_agg(psql.aggregate_order_by(column, column.asc()))


def is_db_retry_error(e: Exception) -> bool:
    return isinstance(e, DBAPIError) and getattr(e.orig, "pgcode", None) == "40001"


async def vacuum_db(
    local_config: LocalConfig | Mapping[str, Any], vacuum_full: bool = False
) -> None:
    async with connect_database(local_config, isolation_level="AUTOCOMMIT") as db:
        async with db.begin() as conn:
            vacuum_sql = "VACUUM FULL" if vacuum_full else "VACUUM"
            log.info(f"Perfoming {vacuum_sql} operation...")
            await conn.exec_driver_sql(vacuum_sql)
