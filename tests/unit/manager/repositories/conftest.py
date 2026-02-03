from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, create_async_engine
from ai.backend.testutils.bootstrap import postgres_container  # noqa: F401


@pytest.fixture
async def database_connection(
    postgres_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """
    Database connection only - no table creation.
    Use with `with_tables` from ai.backend.testutils.db for selective table loading.

    This is a lightweight alternative to `database_engine` that doesn't
    create any tables or run migrations. Tables should be created per-test
    using the `with_tables` context manager.

    Note: This is function-scoped to avoid event loop issues with asyncpg.
    The postgres container itself is session-scoped for efficiency.
    """
    _, addr = postgres_container
    url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"

    engine = create_async_engine(
        url,
        pool_size=8,
        pool_pre_ping=False,
        max_overflow=64,
    )

    yield engine

    await engine.dispose()
