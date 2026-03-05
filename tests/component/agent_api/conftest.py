from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.rest.agent.handler import AgentHandler
from ai.backend.manager.api.rest.agent.registry import register_agent_routes
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent.row import AgentRow


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for agent-api-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_agent_routes(AgentHandler(agent=mock_processors.agent), route_deps),
    ]


@pytest.fixture()
async def agent_fixture(
    db_engine: SAEngine,
    scaling_group_fixture: str,
) -> AsyncIterator[str]:
    """Insert a test agent row and yield its ID.

    The agent references the scaling_group_fixture via FK.
    Teardown deletes the agent row (cascade deletes agent_resources).
    """
    agent_id = f"i-test-agent-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(AgentRow.__table__).values(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=scaling_group_fixture,
                schedulable=True,
                available_slots=ResourceSlot({"cpu": "4", "mem": "8589934592"}),
                occupied_slots=ResourceSlot(),
                addr="tcp://127.0.0.1:6011",
                version="24.12.0",
                architecture="x86_64",
                compute_plugins={},
                auto_terminate_abusing_kernel=False,
            )
        )
    yield agent_id
    async with db_engine.begin() as conn:
        await conn.execute(AgentRow.__table__.delete().where(AgentRow.__table__.c.id == agent_id))
