from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import HealthCheckerRegistration
from ai.backend.common.health_checker import HealthCheckKey
from ai.backend.common.health_checker.types import DATABASE, ComponentId
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.health.database import DatabaseHealthChecker
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, connect_database

from .base import InfrastructureDependency


class DatabaseDependency(InfrastructureDependency[ExtendedAsyncSAEngine]):
    """Provides database connection lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "database"

    @asynccontextmanager
    async def provide(
        self, setup_input: ManagerUnifiedConfig
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        """Initialize and provide a database connection.

        Args:
            setup_input: Configuration containing database settings

        Yields:
            Initialized ExtendedAsyncSAEngine
        """
        async with connect_database(setup_input.db) as db:
            yield db

    def gen_health_checkers(
        self,
        resource: ExtendedAsyncSAEngine,
    ) -> list[HealthCheckerRegistration]:
        """
        Return database health checker.

        Args:
            resource: The initialized database engine

        Returns:
            List containing health checker registration for PostgreSQL database
        """
        return [
            HealthCheckerRegistration(
                key=HealthCheckKey(service_group=DATABASE, component_id=ComponentId("postgres")),
                checker=DatabaseHealthChecker(db=resource),
            )
        ]
