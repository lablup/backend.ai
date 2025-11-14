from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import DependencyProvider

from ...config import ServerConfig
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
