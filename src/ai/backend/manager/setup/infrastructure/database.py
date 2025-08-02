from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from urllib.parse import quote as urlquote

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from ai.backend.common.json import ExtendedJSONEncoder
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.base import pgsql_connect_opts
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class DatabaseSpec:
    config: ManagerUnifiedConfig


class DatabaseProvisioner(Provisioner[DatabaseSpec, ExtendedAsyncSAEngine]):
    @property
    def name(self) -> str:
        return "database"

    async def setup(self, spec: DatabaseSpec) -> ExtendedAsyncSAEngine:
        db_config = spec.config.db
        addr = db_config.addr
        username = db_config.user
        password = db_config.password
        dbname = db_config.name

        if password is None:
            raise RuntimeError("password is required for database connection")

        address = addr.to_legacy()
        url = f"postgresql+asyncpg://{urlquote(username)}:{urlquote(password)}@{address}/{urlquote(dbname)}"

        # Check PostgreSQL version to adjust connection options
        version_check_db = create_async_engine(url)
        async with version_check_db.begin() as conn:
            result = await conn.execute(sa.text("show server_version"))
            version_str = result.scalar()
            major, minor, *_ = map(int, version_str.partition(" ")[0].split("."))
            if (major, minor) < (11, 0):
                pgsql_connect_opts["server_settings"].pop("jit", None)
        await version_check_db.dispose()

        # Create the extended async engine with all configurations
        db = ExtendedAsyncSAEngine(
            create_async_engine(
                url,
                connect_args=pgsql_connect_opts,
                pool_size=db_config.pool_size,
                pool_recycle=db_config.pool_recycle,
                pool_pre_ping=db_config.pool_pre_ping,
                max_overflow=db_config.max_overflow,
                json_serializer=functools.partial(json.dumps, cls=ExtendedJSONEncoder),
                isolation_level="SERIALIZABLE",
                future=True,
            ),
            txn_concurrency_threshold=max(
                int(db_config.pool_size + max(0, db_config.max_overflow) * 0.5),
                2,
            ),
            lock_conn_timeout=int(db_config.lock_conn_timeout),
        )

        return db

    async def teardown(self, resource: ExtendedAsyncSAEngine) -> None:
        # Dispose of all database connections
        await resource.dispose()
