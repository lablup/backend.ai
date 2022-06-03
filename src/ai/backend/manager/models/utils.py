from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager as actxmgr
import functools
import json
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Mapping,
    Tuple,
    TypeVar,
)
from urllib.parse import quote_plus as urlquote

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.engine import create_engine as _create_engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import (
    AsyncConnection as SAConnection,
    AsyncEngine as SAEngine,
    AsyncSession as SASession,
)
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

log = BraceStyleAdapter(logging.getLogger(__name__))
column_constraints = ['nullable', 'index', 'unique', 'primary_key']

# TODO: Implement begin(), begin_readonly() for AsyncSession also


class ExtendedAsyncSAEngine(SAEngine):
    """
    A subclass to add a few more convenience methods to the SQLAlchemy's async engine.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._readonly_txn_count = 0
        self._generic_txn_count = 0
        self._txn_concurrency_threshold = kwargs.pop("txn_concurrency_threshold", 8)

    @actxmgr
    async def begin(self) -> AsyncIterator[SAConnection]:
        async with super().begin() as conn:
            self._generic_txn_count += 1
            if self._generic_txn_count >= self._txn_concurrency_threshold:
                log.warning(
                    "The number of concurrent generic transaction ({}) exceeded the threshold {}.",
                    self._generic_txn_count, self._txn_concurrency_threshold,
                    stack_info=False,
                )
            try:
                yield conn
            finally:
                self._generic_txn_count -= 1

    @actxmgr
    async def begin_readonly(self, deferrable: bool = False) -> AsyncIterator[SAConnection]:
        async with self.connect() as conn:
            self._readonly_txn_count += 1
            if self._readonly_txn_count >= self._txn_concurrency_threshold:
                log.warning(
                    "The number of concurrent read-only transaction ({}) exceeded the threshold {}.",
                    self._readonly_txn_count, self._txn_concurrency_threshold,
                    stack_info=False,
                )
            conn_with_exec_opts = await conn.execution_options(
                postgresql_readonly=True,
                postgresql_deferrable=deferrable,
            )
            async with conn_with_exec_opts.begin():
                try:
                    yield conn_with_exec_opts
                finally:
                    self._readonly_txn_count -= 1

    @actxmgr
    async def begin_session(self) -> AsyncIterator[SASession]:
        async with self.begin() as conn:
            session = SASession(bind=conn)
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    @actxmgr
    async def begin_readonly_session(self, deferrable: bool = False) -> AsyncIterator[SASession]:
        async with self.begin_readonly(deferrable=deferrable) as conn:
            yield SASession(bind=conn)

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
                await lock_conn.exec_driver_sql(
                    f"SELECT pg_advisory_lock({lock_id:d});",
                )
            except sa.exc.DBAPIError as e:
                if getattr(e.orig, 'pgcode', None) == '55P03':  # lock not available error
                    # This may happen upon shutdown after some time.
                    raise asyncio.CancelledError()
                raise
            except asyncio.CancelledError:
                raise
            else:
                lock_acquired = True
                yield
            finally:
                if lock_acquired and not lock_conn.closed:
                    await lock_conn.exec_driver_sql(
                        f"SELECT pg_advisory_unlock({lock_id:d})",
                    )


def create_async_engine(*args, **kwargs) -> ExtendedAsyncSAEngine:
    kwargs["future"] = True
    sync_engine = _create_engine(*args, **kwargs)
    return ExtendedAsyncSAEngine(sync_engine)


@actxmgr
async def connect_database(
    local_config: LocalConfig | Mapping[str, Any],
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    from .base import pgsql_connect_opts
    username = local_config['db']['user']
    password = local_config['db']['password']
    address = local_config['db']['addr']
    dbname = local_config['db']['name']
    url = f"postgresql+asyncpg://{urlquote(username)}:{urlquote(password)}@{address}/{urlquote(dbname)}"

    version_check_db = create_async_engine(url)
    async with version_check_db.begin() as conn:
        result = await conn.execute(sa.text("show server_version"))
        major, minor, *_ = map(int, result.scalar().split("."))
        if (major, minor) < (11, 0):
            pgsql_connect_opts['server_settings'].pop("jit")
    await version_check_db.dispose()

    db = create_async_engine(
        url,
        connect_args=pgsql_connect_opts,
        pool_size=8,
        max_overflow=64,
        json_serializer=functools.partial(json.dumps, cls=ExtendedJSONEncoder),
        isolation_level="SERIALIZABLE",
        future=True,
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


TQueryResult = TypeVar('TQueryResult')


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
                    if getattr(e.orig, 'pgcode', None) == '40001':
                        raise TryAgain
                    raise
    except RetryError:
        raise RuntimeError(f"DB serialization failed after {max_attempts} retries")
    assert result is not Sentinel.token
    return result


def sql_json_merge(
    col,
    key: Tuple[str, ...],
    obj: Mapping[str, Any],
    *,
    _depth: int = 0,
):
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
        sa.func.jsonb_build_object(
            key[_depth],
            (
                sa.func.coalesce(col[key], sa.text("'{}'::jsonb"))
                .concat(sa.func.cast(obj, psql.JSONB))
                if _depth == len(key) - 1
                else sql_json_merge(col, key, obj=obj, _depth=_depth + 1)
            ),
        ),
    )
    return expr


def sql_json_increment(
    col,
    key: Tuple[str, ...],
    *,
    parent_updates: Mapping[str, Any] = None,
    _depth: int = 0,
):
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
    name = column_attrs.pop('name')
    return sa.Column(name, column.type, **{k: column_attrs[k] for k in column_constraints})


def regenerate_table(table: sa.Table, new_metadata: sa.MetaData) -> sa.Table:
    '''
    This function can be used to regenerate table which belongs to SQLAlchemy ORM Class,
    which can be helpful when you're tring to build fresh new table for use on diffrent context
    than main manager logic (e.g. test code).
    Check out tests/test_image.py for more details.
    '''
    return sa.Table(
        table.name, new_metadata,
        *[_populate_column(c) for c in table.columns],
    )
