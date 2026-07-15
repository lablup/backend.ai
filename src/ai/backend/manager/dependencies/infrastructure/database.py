from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.health_checker import ServiceHealthChecker
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.health.database import DatabaseHealthChecker
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.db.engine import connect_database

from .base import InfrastructureDependency


class DatabaseDependency(InfrastructureDependency[ExtendedAsyncSAEngine]):
    """Provides database connection lifecycle management."""

    @property
    @override
    def stage_name(self) -> str:
        return "database"

    @asynccontextmanager
    @override
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

    @override
    def gen_readiness_checker(
        self,
        resource: ExtendedAsyncSAEngine,
    ) -> ServiceHealthChecker:
        """Readiness only — DB unreachable should drain traffic, not trigger restart."""
        return DatabaseHealthChecker(db=resource)
