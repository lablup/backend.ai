"""Runs the session designated agents move against a real database.

The tables it reads are created in a separate schema in their shape before the move, which
the functions reach through `search_path`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from typing import Final

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Connection

from ai.backend.manager.models.alembic.versions import (
    c5ea6e2fa389_move_session_designated_agents_to_a_table as revision,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

_SCHEMA: Final[str] = "session_designated_agent_probe"

_TABLES: Final[tuple[str, ...]] = (
    "CREATE TABLE agents (id VARCHAR(64) PRIMARY KEY, uuid UUID NOT NULL UNIQUE)",
    """CREATE TABLE sessions (
        id UUID PRIMARY KEY,
        status VARCHAR(64) NOT NULL,
        status_info VARCHAR,
        terminated_at TIMESTAMP WITH TIME ZONE,
        status_history JSONB,
        options JSONB NOT NULL,
        designated_agent_ids VARCHAR[]
    )""",
    """CREATE TABLE kernels (
        id UUID PRIMARY KEY,
        session_id UUID NOT NULL,
        status VARCHAR(64) NOT NULL,
        status_info VARCHAR,
        status_changed TIMESTAMP WITH TIME ZONE,
        terminated_at TIMESTAMP WITH TIME ZONE,
        status_history JSONB
    )""",
    """CREATE TABLE resource_allocations (
        kernel_id UUID NOT NULL,
        slot_name VARCHAR(64) NOT NULL,
        free_at TIMESTAMP WITH TIME ZONE
    )""",
    """CREATE TABLE session_designated_agents (
        id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
        session_id UUID NOT NULL,
        agent_uuid UUID NOT NULL,
        PRIMARY KEY (session_id, agent_uuid)
    )""",
)

_LIVE_AGENT: Final[str] = "i-live"
_LIVE_AGENT_UUID: Final[uuid.UUID] = uuid.uuid4()
_GONE_AGENT: Final[str] = "i-gone"

_STRICT_ON_GONE: Final[uuid.UUID] = uuid.uuid4()
_STRICT_ON_GONE_KERNEL: Final[uuid.UUID] = uuid.uuid4()
_PREFERRED_ON_BOTH: Final[uuid.UUID] = uuid.uuid4()
_ENDED_ON_BOTH: Final[uuid.UUID] = uuid.uuid4()
_STRICT_ON_LIVE: Final[uuid.UUID] = uuid.uuid4()

# session id -> (status, policy, designated agent ids)
_SESSIONS: Final[dict[uuid.UUID, tuple[str, str, list[str]]]] = {
    _STRICT_ON_GONE: ("PENDING", "strict", [_GONE_AGENT]),
    _PREFERRED_ON_BOTH: ("PENDING", "preferred", [_LIVE_AGENT, _GONE_AGENT]),
    _ENDED_ON_BOTH: ("TERMINATED", "strict", [_LIVE_AGENT, _GONE_AGENT]),
    _STRICT_ON_LIVE: ("PENDING", "strict", [_LIVE_AGENT]),
}


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with database_connection.begin() as conn:
        await conn.execute(sa.text(f"CREATE SCHEMA {_SCHEMA}"))
        await conn.execute(sa.text(f"SET LOCAL search_path TO {_SCHEMA}"))
        for statement in _TABLES:
            await conn.execute(sa.text(statement))
        await conn.execute(
            sa.text("INSERT INTO agents (id, uuid) VALUES (:id, :uuid)").bindparams(
                id=_LIVE_AGENT, uuid=_LIVE_AGENT_UUID
            )
        )
        for session_id, (status, policy, agent_ids) in _SESSIONS.items():
            await conn.execute(
                sa.text(
                    "INSERT INTO sessions (id, status, options, designated_agent_ids)"
                    " VALUES (:id, :status, jsonb_build_object('agent_selection_policy',"
                    " CAST(:policy AS text)), :agent_ids)"
                ).bindparams(id=session_id, status=status, policy=policy, agent_ids=agent_ids)
            )
        await conn.execute(
            sa.text(
                "INSERT INTO kernels (id, session_id, status) VALUES (:id, :session_id, 'PENDING')"
            ).bindparams(id=_STRICT_ON_GONE_KERNEL, session_id=_STRICT_ON_GONE)
        )
        await conn.execute(
            sa.text(
                "INSERT INTO resource_allocations (kernel_id, slot_name) VALUES (:kernel_id, 'cpu')"
            ).bindparams(kernel_id=_STRICT_ON_GONE_KERNEL)
        )
    try:
        yield database_connection
    finally:
        async with database_connection.begin() as conn:
            await conn.execute(sa.text(f"DROP SCHEMA {_SCHEMA} CASCADE"))


async def _run(db: ExtendedAsyncSAEngine, step: Callable[[Connection], None]) -> None:
    async with db.begin() as conn:
        await conn.execute(sa.text(f"SET LOCAL search_path TO {_SCHEMA}"))
        await conn.run_sync(step)


async def _move(db: ExtendedAsyncSAEngine) -> None:
    await _run(db, revision.cancel_unplaceable_sessions)
    await _run(db, revision.backfill_designations)


async def _designations(db: ExtendedAsyncSAEngine) -> set[tuple[uuid.UUID, uuid.UUID]]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(
            sa.text(f"SELECT session_id, agent_uuid FROM {_SCHEMA}.session_designated_agents")
        )
        return {(row.session_id, row.agent_uuid) for row in rows}


async def _statuses(db: ExtendedAsyncSAEngine) -> dict[uuid.UUID, str]:
    async with db.begin_readonly() as conn:
        rows = await conn.execute(sa.text(f"SELECT id, status FROM {_SCHEMA}.sessions"))
        return {row.id: row.status for row in rows}


class TestMoveSessionDesignatedAgents:
    async def test_only_the_agents_still_in_agents_become_rows(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _move(db)

        assert await _designations(db) == {
            (_PREFERRED_ON_BOTH, _LIVE_AGENT_UUID),
            (_ENDED_ON_BOTH, _LIVE_AGENT_UUID),
            (_STRICT_ON_LIVE, _LIVE_AGENT_UUID),
        }

    async def test_only_a_pending_strict_session_on_a_gone_agent_is_cancelled(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _move(db)

        assert await _statuses(db) == {
            _STRICT_ON_GONE: "CANCELLED",
            _PREFERRED_ON_BOTH: "PENDING",
            _ENDED_ON_BOTH: "TERMINATED",
            _STRICT_ON_LIVE: "PENDING",
        }

    async def test_the_cancelled_session_records_why_and_frees_its_kernels(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _move(db)

        async with db.begin_readonly() as conn:
            session = (
                await conn.execute(
                    sa.text(
                        f"SELECT status_info, terminated_at, status_history"
                        f" FROM {_SCHEMA}.sessions WHERE id = :id"
                    ).bindparams(id=_STRICT_ON_GONE)
                )
            ).one()
            kernel = (
                await conn.execute(sa.text(f"SELECT status, status_info FROM {_SCHEMA}.kernels"))
            ).one()
            free_at = await conn.scalar(
                sa.text(f"SELECT free_at FROM {_SCHEMA}.resource_allocations")
            )
        assert session.status_info == revision.CANCEL_REASON
        assert session.terminated_at is not None
        assert "CANCELLED" in session.status_history
        assert (kernel.status, kernel.status_info) == ("CANCELLED", revision.CANCEL_REASON)
        assert free_at is not None

    async def test_running_it_twice_leaves_the_same_rows(self, db: ExtendedAsyncSAEngine) -> None:
        await _move(db)
        first = await _designations(db)

        await _move(db)

        assert await _designations(db) == first

    async def test_the_downgrade_writes_the_rows_back_into_the_arrays(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        await _move(db)
        async with db.begin() as conn:
            await conn.execute(
                sa.text(f"UPDATE {_SCHEMA}.sessions SET designated_agent_ids = NULL")
            )

        await _run(db, revision.restore_designations)

        async with db.begin_readonly() as conn:
            rows = await conn.execute(
                sa.text(f"SELECT id, designated_agent_ids FROM {_SCHEMA}.sessions")
            )
            restored = {row.id: row.designated_agent_ids for row in rows}
        assert restored == {
            _STRICT_ON_GONE: None,
            _PREFERRED_ON_BOTH: [_LIVE_AGENT],
            _ENDED_ON_BOTH: [_LIVE_AGENT],
            _STRICT_ON_LIVE: [_LIVE_AGENT],
        }
