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
    """Function-scoped DB engine without table creation.

    Mirrors `tests/unit/manager/repositories/conftest.py` so validator tests can
    seed RBAC tables on demand via `with_tables`.
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
