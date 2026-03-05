"""Database source for login session repository operations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.login_session.types import LoginSessionData, LoginSessionExpiryReason
from ai.backend.manager.models.login_session.row import LoginSessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LoginSessionDBSource:
    """Database source for login session CRUD operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_session(
        self,
        user_uuid: UUID,
        session_token: str,
        client_ip: str,
    ) -> LoginSessionData:
        """Insert a new login session row."""
        async with self._db.begin_session() as session:
            row = LoginSessionRow(
                user_uuid=user_uuid,
                session_token=session_token,
                client_ip=client_ip,
            )
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return row.to_dataclass()

    async def expire_session(
        self,
        session_token: str,
        reason: LoginSessionExpiryReason,
    ) -> LoginSessionData | None:
        """Mark a session as expired by setting expired_at and reason."""
        async with self._db.begin_session() as db_sess:
            row = await self._get_active_session(db_sess, session_token)
            if row is None:
                return None
            row.expired_at = datetime.now(tz=UTC)
            row.reason = reason
            return row.to_dataclass()

    async def list_active_sessions(self, user_uuid: UUID) -> list[LoginSessionData]:
        """List all active (non-expired) sessions for a user."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(LoginSessionRow).where(
                sa.and_(
                    LoginSessionRow.user_uuid == user_uuid,
                    LoginSessionRow.expired_at.is_(None),
                )
            )
            rows = await db_sess.scalars(query)
            return [row.to_dataclass() for row in rows]

    async def count_active_sessions(self, user_uuid: UUID) -> int:
        """Count active (non-expired) sessions for a user."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = (
                sa.select(sa.func.count())
                .where(
                    sa.and_(
                        LoginSessionRow.user_uuid == user_uuid,
                        LoginSessionRow.expired_at.is_(None),
                    )
                )
                .select_from(LoginSessionRow)
            )
            result = await db_sess.scalar(query)
            return int(result) if result is not None else 0

    async def _get_active_session(
        self, db_sess: SASession, session_token: str
    ) -> LoginSessionRow | None:
        return cast(
            LoginSessionRow | None,
            await db_sess.scalar(
                sa.select(LoginSessionRow).where(
                    sa.and_(
                        LoginSessionRow.session_token == session_token,
                        LoginSessionRow.expired_at.is_(None),
                    )
                )
            ),
        )
