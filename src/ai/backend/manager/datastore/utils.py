from contextlib import asynccontextmanager as actxmgr
from typing import Any, AsyncIterator, Mapping
from urllib.parse import quote_plus as urlquote

from sqlalchemy.ext.asyncio import AsyncEngine as SAEngine
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine
from sqlalchemy.pool import NullPool

from .config import pool_connect_opts


@actxmgr
async def connect_database(
    local_config: Mapping[str, Any],
    isolation_level: str = "SERIALIZABLE",
) -> AsyncIterator[SAEngine]:
    username = local_config["db-pooler"]["user"]
    password = local_config["db-pooler"]["password"]
    address = local_config["db-pooler"]["addr"]
    dbname = local_config["db-pooler"]["name"]

    url = f"postgresql+asyncpg://{urlquote(username)}:{urlquote(password)}@{address}/{urlquote(dbname)}"
    engine = _create_async_engine(
        url,
        poolclass=NullPool,
        future=True,
        connect_args=pool_connect_opts,
    )
    yield engine
    await engine.dispose()
