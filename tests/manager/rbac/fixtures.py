import secrets
from pathlib import Path
from typing import AsyncIterator

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.pool import NullPool

from ai.backend.common.types import HostPortPair
from ai.backend.logging import is_active as logging_active
from ai.backend.manager.models.alembic import invoked_programmatically
from ai.backend.manager.models.base import metadata, pgsql_connect_opts

ALEMBIC_CONFIG_PATH = Path("alembic.ini")


@pytest.fixture
def test_db_name() -> str:
    """Generate a unique database name for testing."""
    return f"test_vfolder_rbac_{secrets.token_hex(8)}"


@pytest.fixture
def test_db_url(postgres_container: tuple[str, HostPortPair], test_db_name: str) -> str:
    """Create a database URL for the test database."""
    _, host_port = postgres_container
    db_user = "postgres"
    db_password = "develove"
    return f"postgresql+asyncpg://{db_user}:{db_password}@{host_port.host}:{host_port.port}/{test_db_name}"


@pytest.fixture
def admin_db_url(postgres_container: tuple[str, HostPortPair]) -> str:
    """Create a database URL for the admin database."""
    _, host_port = postgres_container
    db_user = "postgres"
    db_password = "develove"
    return f"postgresql+asyncpg://{db_user}:{db_password}@{host_port.host}:{host_port.port}/testing"


@pytest.fixture
def alembic_config(test_db_url: str) -> Config:
    """Create Alembic configuration for testing."""
    config = Config(ALEMBIC_CONFIG_PATH)
    config.set_main_option("script_location", "src/ai/backend/manager/models/alembic")
    config.set_main_option("sqlalchemy.url", test_db_url)
    logging_active.set(True)  # Why??
    return config


@pytest.fixture
async def db_engine_pre_migration(
    postgres_container: tuple[str, HostPortPair],
    test_db_name: str,
    alembic_config: Config,
    test_db_url: str,
    admin_db_url: str,
) -> AsyncIterator[Engine]:
    """
    Create a database engine with schema migrated up to revision 643deb439458.
    This is the state before the vfolder RBAC migration.
    """
    # First create the test database
    admin_engine = sa.ext.asyncio.create_async_engine(
        admin_db_url, poolclass=NullPool, isolation_level="AUTOCOMMIT"
    )

    def drop_and_create_db(connection: Connection) -> None:
        """Drop the test database if it exists and create a new one."""
        alembic_config.attributes["connection"] = connection
        connection.execute(sa.text(f'DROP DATABASE IF EXISTS "{test_db_name}";'))
        connection.execute(sa.text(f'CREATE DATABASE "{test_db_name}"'))

    async with admin_engine.connect() as conn:
        await conn.run_sync(drop_and_create_db)

    # Create engine for the test database
    engine = sa.ext.asyncio.create_async_engine(
        test_db_url,
        poolclass=NullPool,
        echo=False,
        connect_args=pgsql_connect_opts,
    )

    invoked_programmatically.set(True)

    def create_all(connection: Connection, engine: Engine) -> None:
        alembic_config.attributes["connection"] = connection
        # Create extension in the same connection context
        metadata.create_all(engine, checkfirst=False)
        target_revision = "643deb439458"  # The revision before vfolder RBAC migration
        connection.exec_driver_sql("CREATE TABLE alembic_version (\nversion_num varchar(32)\n);")
        connection.exec_driver_sql(f"INSERT INTO alembic_version VALUES('{target_revision}')")

    async with engine.connect() as dbconn:
        async with dbconn.begin():
            await dbconn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            await dbconn.commit()
        async with dbconn.begin():
            await dbconn.run_sync(create_all, engine=engine.sync_engine)

    yield engine

    # Cleanup: close connections and drop database
    await engine.dispose()

    def terminate(connection: Connection) -> None:
        """Terminate all connections to the test database and drop it."""
        alembic_config.attributes["connection"] = connection
        connection.execute(
            sa.text(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid()"
            )
        )
        connection.execute(sa.text(f"DROP DATABASE IF EXISTS {test_db_name}"))

    async with admin_engine.connect() as conn:
        await conn.run_sync(terminate)
    await admin_engine.dispose()


@pytest.fixture
async def db_connection_pre_migration(db_engine_pre_migration: Engine):
    """Provide a database connection for the pre-migration state."""
    async with db_engine_pre_migration.connect() as conn:
        async with conn.begin():
            yield conn
