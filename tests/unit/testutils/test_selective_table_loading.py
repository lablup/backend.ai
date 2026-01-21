"""
Test for selective table loading infrastructure (BA-3612).
"""

from __future__ import annotations

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.base import Base
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestSampleRow(Base):
    __tablename__ = "test_sample"
    name = sa.Column(sa.String(64), primary_key=True)


@pytest.mark.asyncio
async def test_with_tables_creates_and_truncates(
    database_connection: ExtendedAsyncSAEngine,
) -> None:
    """Test that with_tables creates tables and cleans up via TRUNCATE CASCADE."""
    sample_name = "test-sample"

    async with with_tables(database_connection, [TestSampleRow]):
        # Insert a row
        async with database_connection.begin_session() as db_sess:
            row = TestSampleRow(name=sample_name)
            db_sess.add(row)
            await db_sess.commit()

        # Verify it exists
        async with database_connection.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(TestSampleRow).where(TestSampleRow.name == sample_name)
            )
            fetched = result.scalar_one_or_none()
            assert fetched is not None
            assert fetched.name == sample_name

    # After exiting context, table should be truncated
    async with database_connection.begin_readonly_session() as db_sess:
        result = await db_sess.execute(sa.select(sa.func.count()).select_from(TestSampleRow))
        count = result.scalar()
        assert count == 0
