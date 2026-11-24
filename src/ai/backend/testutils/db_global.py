from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from ai.backend.manager.models.global_entity.row import GlobalEntityRow
from ai.backend.manager.models.global_entity.seed import SEED_GLOBAL_ENTITIES_SQL
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import TableOrORM, with_tables


@asynccontextmanager
async def with_global_entities(engine: AsyncEngine) -> AsyncGenerator[None]:
    """
    Create the global entity rows and their virtual entities, as the migration does.
    Tables are truncated on exit.
    """
    tables: list[TableOrORM] = [
        GlobalEntityRow,
        VirtualEntityRow,
        EntityMembershipRow,
        ScopeBindingRow,
    ]
    async with with_tables(engine, tables):
        async with engine.begin() as conn:
            for statement in SEED_GLOBAL_ENTITIES_SQL:
                await conn.execute(text(statement))
        yield
