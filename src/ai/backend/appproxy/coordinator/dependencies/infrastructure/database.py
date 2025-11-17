from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import ServiceHealthChecker

from ...config import ServerConfig
from ...health.database import DatabaseHealthChecker
from ...models.utils import ExtendedAsyncSAEngine, connect_database


class DatabaseProvider(DependencyProvider[ServerConfig, ExtendedAsyncSAEngine]):
    """Provider for PostgreSQL database connection."""

    @property
    def stage_name(self) -> str:
        return "database"

    @asynccontextmanager
    async def provide(self, setup_input: ServerConfig) -> AsyncIterator[ExtendedAsyncSAEngine]:
        """Create and provide database connection."""
        async with connect_database(setup_input.db) as db:
            yield db

    def gen_health_checkers(self, resource: ExtendedAsyncSAEngine) -> ServiceHealthChecker:
        """
        Return database health checker.

        Args:
            resource: The initialized database engine

        Returns:
            Health checker for PostgreSQL database
        """
        return DatabaseHealthChecker(db=resource)
