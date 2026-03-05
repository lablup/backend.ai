"""LoginSession service."""

from __future__ import annotations

import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.login_session import LoginSessionRepository
from ai.backend.manager.services.login_session.actions.check_concurrency_limit import (
    CheckConcurrencyLimitAction,
    CheckConcurrencyLimitActionResult,
)
from ai.backend.manager.services.login_session.actions.create_session import (
    CreateLoginSessionAction,
    CreateLoginSessionActionResult,
)
from ai.backend.manager.services.login_session.actions.evict_oldest_session import (
    EvictOldestSessionAction,
    EvictOldestSessionActionResult,
)
from ai.backend.manager.services.login_session.actions.expire_session import (
    ExpireLoginSessionAction,
    ExpireLoginSessionActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LoginSessionService:
    _repository: LoginSessionRepository

    def __init__(self, repository: LoginSessionRepository) -> None:
        self._repository = repository

    async def create_session(
        self, action: CreateLoginSessionAction
    ) -> CreateLoginSessionActionResult:
        session = await self._repository.create_session(
            user_uuid=action.user_uuid,
            session_token=action.session_token,
            client_ip=action.client_ip,
        )
        return CreateLoginSessionActionResult(session=session)

    async def expire_session(
        self, action: ExpireLoginSessionAction
    ) -> ExpireLoginSessionActionResult:
        session = await self._repository.expire_session(
            user_uuid=action.user_uuid,
            session_token=action.session_token,
            reason=action.reason,
        )
        return ExpireLoginSessionActionResult(session=session)

    async def evict_oldest_session(
        self, action: EvictOldestSessionAction
    ) -> EvictOldestSessionActionResult:
        evicted_token = await self._repository.evict_oldest_session(action.user_uuid)
        return EvictOldestSessionActionResult(evicted_session_token=evicted_token)

    async def check_concurrency_limit(
        self, action: CheckConcurrencyLimitAction
    ) -> CheckConcurrencyLimitActionResult:
        active_sessions = await self._repository.count_active_sessions(action.user_uuid)
        limit_exceeded = (
            action.max_concurrent_logins is not None
            and active_sessions >= action.max_concurrent_logins
        )
        return CheckConcurrencyLimitActionResult(
            active_sessions=active_sessions,
            limit_exceeded=limit_exceeded,
        )
