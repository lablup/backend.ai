from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.health.database import DatabaseHealthChecker
from ai.backend.appproxy.coordinator.models.utils import ExtendedAsyncSAEngine, connect_database
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import ServiceHealthChecker


class DatabaseProvider(DependencyProvider[ServerConfig, ExtendedAsyncSAEngine]):
    """Provider for PostgreSQL database connection."""

    @property
    @override
    def stage_name(self) -> str:
        return "database"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: ServerConfig) -> AsyncIterator[ExtendedAsyncSAEngine]:
        """Create and provide database connection."""
        async with connect_database(setup_input.db) as db:
            yield db

    @override
    def gen_readiness_checker(self, resource: ExtendedAsyncSAEngine) -> ServiceHealthChecker:
        """Readiness only — DB unreachable should drain traffic, not trigger restart."""
        return DatabaseHealthChecker(db=resource)
