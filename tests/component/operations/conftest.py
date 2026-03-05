from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.error_log.handler import ErrorLogHandler
from ai.backend.manager.api.rest.error_log.registry import register_error_log_routes
from ai.backend.manager.api.rest.manager.handler import ManagerHandler
from ai.backend.manager.api.rest.manager.registry import register_manager_api_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.agent import agents
from ai.backend.manager.models.error_logs import error_logs


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for operations-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_error_log_routes(ErrorLogHandler(error_log=mock_processors.error_log), route_deps),
        register_manager_api_routes(
            ManagerHandler(manager_admin=mock_processors.manager_admin), route_deps
        ),
    ]


@pytest.fixture()
async def agent_fixture(
    db_engine: SAEngine,
    scaling_group_fixture: str,
) -> AsyncIterator[str]:
    """Insert a test agent record and yield its ID."""
    agent_id = f"i-test-agent-{secrets.token_hex(4)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(agents).values(
                id=agent_id,
                region="local",
                scaling_group=scaling_group_fixture,
                available_slots=ResourceSlot(),
                occupied_slots=ResourceSlot(),
                addr="127.0.0.1:6001",
                version="test",
                architecture="x86_64",
            )
        )
    yield agent_id


@pytest.fixture(autouse=True)
async def _cleanup_side_effects(
    db_engine: SAEngine,
    server: Any,
) -> AsyncIterator[None]:
    """Clean error_logs and agents tables after each test.

    Depends on ``server`` to ensure teardown runs before user/scaling-group
    fixture teardowns, which would otherwise hit FK violations.
    """
    yield
    async with db_engine.begin() as conn:
        await conn.execute(sa.delete(error_logs))
        await conn.execute(sa.delete(agents))
