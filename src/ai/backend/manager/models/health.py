from __future__ import annotations

import os
import socket
from typing import TYPE_CHECKING, cast

from pydantic import (
    BaseModel,
    Field,
)
from redis.asyncio import ConnectionPool
from sqlalchemy.pool import Pool

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import (
    RedisConnectionInfo,
    RedisHelperConfig,
)

if TYPE_CHECKING:
    from ..api.context import RootContext


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
    num_connections: int | None = Field(
        description="The number of connections in Redis Client's connection pool."
    )
    max_connections: int
    err_msg: str | None = Field(
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
    shared_config = root_ctx.shared_config

    redis_connection_infos: tuple[RedisConnectionInfo, ...] = (
        root_ctx.redis_live,
        root_ctx.redis_stat,
        root_ctx.redis_image,
        root_ctx.redis_stream,
        root_ctx.redis_lock,
    )
    redis_objects = []
    for info in redis_connection_infos:
        err_msg = None
        num_connections = None
        try:
            pool = cast(ConnectionPool, info.client.connection_pool)
            num_connections = cast(int, pool._created_connections)  # type: ignore[attr-defined]
            max_connections = pool.max_connections
        except Exception as e:
            redis_config = cast(
                RedisHelperConfig, shared_config.data["redis"].get("redis_helper_config")
            )
            max_connections = redis_config["max_connections"]
            err_msg = f"Cannot get connection info from `{info.name}`. (e:{str(e)})"
        redis_objects.append(
            RedisObjectConnectionInfo(
                name=info.name,
                max_connections=max_connections,
                num_connections=num_connections,
                err_msg=err_msg,
            )
        )
    return redis_objects


async def _get_connnection_info(root_ctx: RootContext) -> ConnectionInfoOfProcess:
    node_id = root_ctx.local_config["manager"].get("id", socket.gethostname())
    pid = os.getpid()

    sqlalchemy_info = await get_sqlalchemy_connection_info(root_ctx)
    redis_infos = await get_redis_object_info_list(root_ctx)
    return ConnectionInfoOfProcess(
        node_id=node_id, pid=pid, sqlalchemy_info=sqlalchemy_info, redis_connection_info=redis_infos
    )


async def report_manager_status(root_ctx: RootContext) -> None:
    lifetime = cast(float | None, root_ctx.local_config["manager"]["status-lifetime"])
    cxn_info = await _get_connnection_info(root_ctx)
    _data = msgpack.packb(cxn_info.model_dump(mode="json"))

    await redis_helper.execute(
        root_ctx.redis_stat,
        lambda r: r.set(
            _get_connection_status_key(cxn_info.node_id, cxn_info.pid),
            _data,
            ex=lifetime,
        ),
    )
