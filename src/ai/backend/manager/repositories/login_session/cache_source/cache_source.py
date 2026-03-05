"""Cache source for login session repository operations using Valkey Sorted Sets."""

from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_KEY_PREFIX = "login_session"


class LoginSessionCacheSource:
    """
    Cache source for login session operations.
    Uses Valkey Sorted Set keyed by `login_session:{user_uuid}`.
    Score = UNIX timestamp of session creation.
    Member = session_token.
    """

    _valkey_stat: ValkeyStatClient

    def __init__(self, valkey_stat: ValkeyStatClient) -> None:
        self._valkey_stat = valkey_stat

    def _key(self, user_uuid: UUID) -> str:
        return f"{_KEY_PREFIX}:{user_uuid}"

    async def add_session(self, user_uuid: UUID, session_token: str, score: float) -> None:
        """Register a session in the sorted set (ZADD)."""
        await self._valkey_stat.execute_command([
            "ZADD",
            self._key(user_uuid),
            str(score),
            session_token,
        ])

    async def session_score(self, user_uuid: UUID, session_token: str) -> float | None:
        """Check if session exists and return its score (ZSCORE). Returns None if not found."""
        result = await self._valkey_stat.execute_command([
            "ZSCORE",
            self._key(user_uuid),
            session_token,
        ])
        if result is None:
            return None
        return float(result)

    async def count_sessions(self, user_uuid: UUID) -> int:
        """Return number of active sessions for user (ZCARD)."""
        result = await self._valkey_stat.execute_command(["ZCARD", self._key(user_uuid)])
        return int(result) if result is not None else 0

    async def pop_oldest_session(self, user_uuid: UUID) -> str | None:
        """Evict the oldest session (lowest score) and return its token (ZPOPMIN)."""
        result = await self._valkey_stat.execute_command(["ZPOPMIN", self._key(user_uuid)])
        if not result:
            return None
        # ZPOPMIN returns [member, score] interleaved; first element is the member
        member = result[0]
        if isinstance(member, bytes):
            return member.decode()
        return str(member)

    async def remove_session(self, user_uuid: UUID, session_token: str) -> None:
        """Remove a session from the sorted set (ZREM)."""
        await self._valkey_stat.execute_command(["ZREM", self._key(user_uuid), session_token])
