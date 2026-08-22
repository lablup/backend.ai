from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.entity.error_log import ERROR_LOG_FIELD_TYPE
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.registry.types import (
    FieldGroupMeta,
    GroupMeta,
)
from ai.backend.manager.api.rest.error_log.handler import ErrorLogHandler
from ai.backend.manager.api.rest.error_log.registry import register_error_log_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.error_log.actions.lookup_owner import (
    LookupBulkErrorLogOwnerAction,
    LookupErrorLogOwnerAction,
)
from ai.backend.manager.services.user.error_log.processors import ErrorLogProcessors
from ai.backend.testutils.processors import ops_processor_group


@pytest.fixture()
def error_log_processors(database_engine: ExtendedAsyncSAEngine) -> ErrorLogProcessors:
    return ErrorLogProcessors(
        ops_processor_group(database_engine, GroupMeta(USER_ENTITY_TYPE)).field_group(
            FieldGroupMeta(ERROR_LOG_FIELD_TYPE),
            ErrorLogData,
            LookupErrorLogOwnerAction,
            LookupBulkErrorLogOwnerAction,
        )
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
        await conn.execute(sa.delete(ErrorLogRow))
