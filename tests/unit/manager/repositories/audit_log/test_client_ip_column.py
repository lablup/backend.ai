"""Round-trip tests for the ``inet`` client_ip column of ``audit_logs``."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import cast

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestAuditLogClientIP:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [AuditLogRow]):
            yield database_connection

    async def _insert_row(self, db: ExtendedAsyncSAEngine, client_ip: str | None) -> AuditLogID:
        row_id = AuditLogID(uuid.uuid4())
        async with db.begin_session() as db_sess:
            db_sess.add(
                AuditLogRow(
                    id=row_id,
                    action_kind=ActionKind.SINGLE_ENTITY,
                    entity_type="user",
                    operation="create",
                    action_name="user:create",
                    action_id=uuid.uuid4(),
                    description="test",
                    status=OperationStatus.SUCCESS,
                    client_ip=client_ip,
                )
            )
        return row_id

    async def _insert_row_as_raw_inet(
        self, db: ExtendedAsyncSAEngine, client_ip: str
    ) -> AuditLogID:
        """Write the row the way a pre-existing record was written: a bare ``inet`` value."""
        row_id = AuditLogID(uuid.uuid4())
        async with db.begin() as conn:
            await conn.execute(
                sa.text(
                    "INSERT INTO audit_logs"
                    " (id, entity_type, operation, action_name, action_id,"
                    "  description, status, client_ip)"
                    " VALUES (:id, 'user', 'create', 'user:create', :action_id,"
                    "  'test', 'success', CAST(:client_ip AS inet))"
                ),
                {"id": row_id, "action_id": uuid.uuid4(), "client_ip": client_ip},
            )
        return row_id

    async def _read_client_ip(self, db: ExtendedAsyncSAEngine, row_id: AuditLogID) -> str | None:
        async with db.begin_readonly_session() as db_sess:
            row = await db_sess.get(AuditLogRow, row_id)
            assert row is not None
            return row.to_dataclass().client_ip

    async def _stored_value_equals(
        self, db: ExtendedAsyncSAEngine, row_id: AuditLogID, client_ip: str
    ) -> bool:
        """Compare the column against the address as postgres itself parses it."""
        async with db.begin_readonly() as conn:
            result = await conn.execute(
                sa.text(
                    "SELECT client_ip = CAST(:client_ip AS inet) FROM audit_logs WHERE id = :id"
                ),
                {"id": row_id, "client_ip": client_ip},
            )
            return cast(bool, result.scalar_one())

    @pytest.mark.parametrize(
        "client_ip",
        [
            "203.0.113.7",
            "2001:db8:1:2::1",
            # What ``ClientIPMaskingMode.TRUNCATE`` stores: a host address whose host
            # bits are zeroed, which must not come back as a network.
            "203.0.113.0",
            "2001:db8:1::",
        ],
    )
    async def test_an_address_reads_back_as_the_stored_string(
        self, db_with_cleanup: ExtendedAsyncSAEngine, client_ip: str
    ) -> None:
        row_id = await self._insert_row(db_with_cleanup, client_ip)

        value = await self._read_client_ip(db_with_cleanup, row_id)

        assert value == client_ip
        assert isinstance(value, str)

    async def test_a_missing_address_reads_back_as_none(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        row_id = await self._insert_row(db_with_cleanup, None)

        assert await self._read_client_ip(db_with_cleanup, row_id) is None

    @pytest.mark.parametrize("client_ip", ["203.0.113.7", "2001:db8:1:2::1"])
    async def test_the_column_stores_the_address_it_was_given(
        self, db_with_cleanup: ExtendedAsyncSAEngine, client_ip: str
    ) -> None:
        """The stored value is the address itself, so it stays comparable in SQL."""
        row_id = await self._insert_row(db_with_cleanup, client_ip)

        assert await self._stored_value_equals(db_with_cleanup, row_id, client_ip)

    @pytest.mark.parametrize("client_ip", ["203.0.113.7", "2001:db8:1:2::1"])
    async def test_a_row_written_as_raw_inet_reads_back_as_a_string(
        self, db_with_cleanup: ExtendedAsyncSAEngine, client_ip: str
    ) -> None:
        """Rows that predate the column type must read back the same way."""
        row_id = await self._insert_row_as_raw_inet(db_with_cleanup, client_ip)

        assert await self._read_client_ip(db_with_cleanup, row_id) == client_ip

    async def test_an_address_carrying_a_prefix_reads_back_as_a_string(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        """``inet`` also holds prefixed values; reading one must not raise."""
        row_id = await self._insert_row_as_raw_inet(db_with_cleanup, "10.1.2.0/24")

        assert await self._read_client_ip(db_with_cleanup, row_id) == "10.1.2.0/24"

    async def test_an_update_replaces_the_address(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        row_id = await self._insert_row(db_with_cleanup, "203.0.113.7")

        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(AuditLogRow)
                .where(AuditLogRow.id == row_id)
                .values(client_ip="2001:db8:1:2::1")
            )

        assert await self._read_client_ip(db_with_cleanup, row_id) == "2001:db8:1:2::1"
        assert await self._stored_value_equals(db_with_cleanup, row_id, "2001:db8:1:2::1")

    async def test_an_update_can_clear_the_address(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> None:
        row_id = await self._insert_row(db_with_cleanup, "203.0.113.7")

        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(AuditLogRow).where(AuditLogRow.id == row_id).values(client_ip=None)
            )

        assert await self._read_client_ip(db_with_cleanup, row_id) is None
