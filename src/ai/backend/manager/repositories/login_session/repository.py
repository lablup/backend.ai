"""LoginSession repository orchestrating DB and cache sources."""

from __future__ import annotations

import logging
import time
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.login_session.types import LoginSessionData, LoginSessionExpiryReason
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .cache_source.cache_source import LoginSessionCacheSource
from .db_source.db_source import LoginSessionDBSource
from .utils import suppress_with_log

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


login_session_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.LOGIN_SESSION_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class LoginSessionRepository:
    """Repository that orchestrates between DB and cache sources for login session operations."""

    _db_source: LoginSessionDBSource
    _cache_source: LoginSessionCacheSource

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        self._db_source = LoginSessionDBSource(db)
        self._cache_source = LoginSessionCacheSource(valkey_stat)

    @login_session_repository_resilience.apply()
    async def create_session(
        self,
        user_uuid: UUID,
        session_token: str,
        client_ip: str,
    ) -> LoginSessionData:
        """Create a new login session. Writes to DB first, then updates cache."""
        data = await self._db_source.create_session(user_uuid, session_token, client_ip)
        score = data.created_at.timestamp() if data.created_at else time.time()
        with suppress_with_log(
            [Exception], message="Failed to add session to cache after creation"
        ):
            await self._cache_source.add_session(user_uuid, session_token, score)
        return data

    @login_session_repository_resilience.apply()
    async def expire_session(
        self,
        user_uuid: UUID,
        session_token: str,
        reason: LoginSessionExpiryReason,
    ) -> LoginSessionData | None:
        """Expire a session. Writes to DB first, then removes from cache."""
        data = await self._db_source.expire_session(session_token, reason)
        with suppress_with_log(
            [Exception], message="Failed to remove session from cache after expiry"
        ):
            await self._cache_source.remove_session(user_uuid, session_token)
        return data

    @login_session_repository_resilience.apply()
    async def evict_oldest_session(self, user_uuid: UUID) -> str | None:
        """
        Evict the oldest session for a user.
        Pops from cache first; if cache hit, expires in DB. Falls back to DB-only list.
        Returns the evicted session_token or None if no active sessions.
        """
        # Try cache-first
        with suppress_with_log([Exception], message="Failed to pop oldest session from cache"):
            token = await self._cache_source.pop_oldest_session(user_uuid)
            if token is not None:
                await self._db_source.expire_session(token, LoginSessionExpiryReason.EVICTED)
                return token

        # Fallback: list from DB and expire the oldest
        sessions = await self._db_source.list_active_sessions(user_uuid)
        if not sessions:
            return None
        oldest = min(sessions, key=lambda s: s.created_at)
        await self._db_source.expire_session(oldest.session_token, LoginSessionExpiryReason.EVICTED)
        return oldest.session_token

    @login_session_repository_resilience.apply()
    async def count_active_sessions(self, user_uuid: UUID) -> int:
        """
        Count active sessions for a user.
        Cache-first with fallback to DB.
        """
        try:
            return await self._cache_source.count_sessions(user_uuid)
        except Exception as e:
            log.warning("Failed to count sessions from cache: {}", e)
        return await self._db_source.count_active_sessions(user_uuid)

    @login_session_repository_resilience.apply()
    async def list_active_sessions(self, user_uuid: UUID) -> list[LoginSessionData]:
        """List active sessions for a user from DB."""
        return await self._db_source.list_active_sessions(user_uuid)
