from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

_metadata = sa.MetaData()
uuid7_probes = sa.Table(
    "uuid7_probes",
    _metadata,
    sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
)


class TestUUIDGenerateV7:
    @pytest.fixture
    async def db(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncIterator[ExtendedAsyncSAEngine]:
        async with with_tables(database_connection, [uuid7_probes]):
            yield database_connection

    async def _generate(self, db: ExtendedAsyncSAEngine, count: int) -> list[uuid.UUID]:
        async with db.begin_readonly_session() as sess:
            rows = await sess.execute(
                sa.select(sa.func.uuid_generate_v7(type_=sa.Uuid())).select_from(
                    sa.func.generate_series(1, count)
                )
            )
            return [r[0] for r in rows]

    async def test_version_and_variant_bits(self, db: ExtendedAsyncSAEngine) -> None:
        (value,) = await self._generate(db, 1)
        assert value.version == 7
        assert (value.bytes[8] & 0b1100_0000) == 0b1000_0000

    async def test_timestamp_prefix_is_the_generation_time(self, db: ExtendedAsyncSAEngine) -> None:
        before = datetime.now(UTC).timestamp() * 1000
        (value,) = await self._generate(db, 1)
        after = datetime.now(UTC).timestamp() * 1000

        embedded_ms = int.from_bytes(value.bytes[:6], "big")
        assert before - 1000 <= embedded_ms <= after + 1000

    async def test_values_strictly_increase_within_a_session(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        values = await self._generate(db, 1000)
        assert len(set(values)) == len(values)
        assert values == sorted(values)

    async def test_server_default_fills_the_id_column(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as sess:
            for _ in range(3):
                await sess.execute(sa.insert(uuid7_probes))

        async with db.begin_readonly_session() as sess:
            ids = list((await sess.execute(sa.select(uuid7_probes.c.id))).scalars())

        assert len(ids) == 3
        assert all(value.version == 7 for value in ids)
