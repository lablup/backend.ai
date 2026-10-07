from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.manager.data.permission.global_entity import (
    GlobalEntityIDCache,
    global_entity_id,
)
from ai.backend.manager.errors.permission import GlobalEntityMissing, GlobalEntityNotLoaded
from ai.backend.manager.models.global_entity.row import GlobalEntityRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.global_entity.loader import GlobalEntityIDLoader
from ai.backend.testutils.db import with_tables


class TestGlobalEntityIDLoader:
    @pytest.fixture(autouse=True)
    def cleared(self) -> Iterator[None]:
        GlobalEntityIDCache.clear()
        yield
        GlobalEntityIDCache.clear()

    @pytest.fixture
    async def db(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, [GlobalEntityRow, VirtualEntityRow]):
            yield database_connection

    async def _insert_rows(
        self, db: ExtendedAsyncSAEngine, names: list[GlobalEntityName], *, with_nodes: bool
    ) -> None:
        async with db.begin_session() as session:
            for name in names:
                row = GlobalEntityRow(name=name)
                session.add(row)
                await session.flush()
                if with_nodes:
                    session.add(VirtualEntityRow(entity_type=GlobalEntityType(), entity_id=row.id))

    async def test_loads_the_id_of_each_name(
        self, global_entity_ids: ExtendedAsyncSAEngine
    ) -> None:
        async with global_entity_ids.begin_readonly_session() as session:
            rows = (await session.execute(sa.select(GlobalEntityRow))).scalars().all()

        assert {row.name: row.id for row in rows} == {
            name: global_entity_id(name) for name in GlobalEntityName
        }

    async def test_missing_row_raises(self, db: ExtendedAsyncSAEngine) -> None:
        await self._insert_rows(db, [GlobalEntityName.GLOBAL], with_nodes=True)

        with pytest.raises(GlobalEntityMissing):
            await GlobalEntityIDLoader(db).load()
        with pytest.raises(GlobalEntityNotLoaded):
            global_entity_id(GlobalEntityName.GLOBAL)

    async def test_missing_virtual_entity_raises(self, db: ExtendedAsyncSAEngine) -> None:
        await self._insert_rows(db, list(GlobalEntityName), with_nodes=False)

        with pytest.raises(GlobalEntityMissing):
            await GlobalEntityIDLoader(db).load()
