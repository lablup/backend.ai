from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.error_log.handler import ErrorLogHandler
from ai.backend.manager.api.rest.error_log.registry import register_error_log_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.error_logs import error_logs
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.error_log.repository import ErrorLogRepository
from ai.backend.manager.services.error_log.processors import ErrorLogProcessors
from ai.backend.manager.services.error_log.service import ErrorLogService


@pytest.fixture()
def error_log_processors(database_engine: ExtendedAsyncSAEngine) -> ErrorLogProcessors:
    repo = ErrorLogRepository(database_engine)
    service = ErrorLogService(repo)
    return ErrorLogProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    error_log_processors: ErrorLogProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for error-log domain tests."""
    return [
        register_error_log_routes(ErrorLogHandler(error_log=error_log_processors), route_deps),
    ]


@pytest.fixture(autouse=True)
async def _cleanup_error_logs(
    db_engine: SAEngine,
    server: Any,
) -> AsyncIterator[None]:
    """Clean error_logs table after each test to avoid FK violations during teardown."""
    yield
    async with db_engine.begin() as conn:
        await conn.execute(sa.delete(error_logs))
