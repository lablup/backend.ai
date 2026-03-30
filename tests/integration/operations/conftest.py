from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.models.error_logs import error_logs


@pytest.fixture(autouse=True)
async def _cleanup_error_logs(
    db_engine: SAEngine,
    server_factory: Any,
) -> AsyncIterator[None]:
    """Clean error_logs table after each test.

    Depends on ``server_factory`` to ensure teardown runs before user fixture
    teardowns, which would otherwise hit FK violations (error_logs.user →
    users.uuid).
    """
    yield
    async with db_engine.begin() as conn:
        await conn.execute(sa.delete(error_logs))
