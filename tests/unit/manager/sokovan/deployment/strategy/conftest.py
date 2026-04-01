from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, create_async_engine


@pytest.fixture
async def database_connection(
    postgres_container: tuple[str, HostPortPairModel],
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    """Database connection only - no table creation.

    Use with `with_tables` from ai.backend.testutils.db for selective table loading.
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
