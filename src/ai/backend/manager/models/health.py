from __future__ import annotations

import asyncio
import logging
import os
import socket
from typing import TYPE_CHECKING, Optional, cast

import redis.exceptions
from pydantic import (
    BaseModel,
    Field,
)
from sqlalchemy.pool import Pool

from ai.backend.common import msgpack
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ..api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__: tuple[str, ...] = (
    "SQLAlchemyConnectionInfo",
    "RedisObjectConnectionInfo",
    "get_sqlalchemy_connection_info",
    "get_redis_object_info_list",
    "_get_connnection_info",
    "report_manager_status",
)

_sqlalchemy_pool_type_names = (
    "AssertionPool",
    "AsyncAdaptedQueuePool",
    "FallbackAsyncAdaptedQueuePool",
    "NullPool",
    "QueuePool",
    "SingletonThreadPool",
    "StaticPool",
)

MANAGER_STATUS_KEY = "manager.status"


def _get_connection_status_key(node_id: str, pid: int) -> str:
    return f"{MANAGER_STATUS_KEY}.{node_id}:{pid}"


class SQLAlchemyConnectionInfo(BaseModel):
    pool_type: str = Field(
        description=f"Connection pool type of SQLAlchemy engine. One of {_sqlalchemy_pool_type_names}.",
    )
    status_description: str
    num_checkedout_cxn: int = Field(
        description="The number of open connections in SQLAlchemy connection pool.",
    )
    num_checkedin_cxn: int = Field(
        description="The number of closed connections in SQLAlchemy connection pool.",
    )

    @property
    def total_cxn(self) -> int:
        return self.num_checkedout_cxn + self.num_checkedin_cxn


class RedisObjectConnectionInfo(BaseModel):
    name: str
    num_connections: Optional[int] = Field(
        description="The number of connections in Redis Client's connection pool."
    )
    max_connections: int
    err_msg: Optional[str] = Field(
        description="Error message occurred when fetch connection info from Redis client objects.",
        default=None,
    )


class ConnectionInfoOfProcess(BaseModel):
    node_id: str = Field(description="Specified Manager ID or hostname.")
    pid: int = Field(description="Process ID.")
    sqlalchemy_info: SQLAlchemyConnectionInfo
    redis_connection_info: list[RedisObjectConnectionInfo]


async def get_sqlalchemy_connection_info(root_ctx: RootContext) -> SQLAlchemyConnectionInfo:
    pool = cast(Pool, root_ctx.db.pool)
    sqlalchemy_info = SQLAlchemyConnectionInfo(
        pool_type=type(pool).__name__,
        status_description=pool.status(),
        num_checkedout_cxn=pool.checkedout(),
        num_checkedin_cxn=pool.checkedin(),
    )
    return sqlalchemy_info


async def get_redis_object_info_list(root_ctx: RootContext) -> list[RedisObjectConnectionInfo]:
    log.warning("get_redis_object_info_list is deprecated.")
    return []


async def _get_connnection_info(root_ctx: RootContext) -> ConnectionInfoOfProcess:
    node_id = root_ctx.config_provider.config.manager.id or socket.gethostname()
    pid = os.getpid()

    sqlalchemy_info = await get_sqlalchemy_connection_info(root_ctx)
    redis_infos = await get_redis_object_info_list(root_ctx)
    return ConnectionInfoOfProcess(
        node_id=node_id, pid=pid, sqlalchemy_info=sqlalchemy_info, redis_connection_info=redis_infos
    )


async def report_manager_status(root_ctx: RootContext) -> None:
    lifetime = root_ctx.config_provider.config.manager.status_lifetime
    cxn_info = await _get_connnection_info(root_ctx)
    _data = msgpack.packb(cxn_info.model_dump(mode="json"))

    if lifetime is not None:
        await root_ctx.valkey_stat.set_manager_status(
            node_id=cxn_info.node_id,
            pid=cxn_info.pid,
            status_data=_data,
            lifetime=lifetime,
        )


async def get_manager_db_cxn_status(root_ctx: RootContext) -> list[ConnectionInfoOfProcess]:
    cxn_infos: list[ConnectionInfoOfProcess] = []

    try:
        _raw_value = cast(
            list[bytes] | None,
            await root_ctx.valkey_stat.scan_and_get_manager_status(
                f"{MANAGER_STATUS_KEY}*",
            ),
        )
    except (asyncio.TimeoutError, redis.exceptions.ConnectionError):
        # Cannot get data from redis. Return process's own info.
        cxn_infos = [(await _get_connnection_info(root_ctx))]
    else:
        if _raw_value is not None:
            cxn_infos = [
                ConnectionInfoOfProcess.model_validate(msgpack.unpackb(val)) for val in _raw_value
            ]
        else:
            cxn_infos = [(await _get_connnection_info(root_ctx))]
    return cxn_infos
