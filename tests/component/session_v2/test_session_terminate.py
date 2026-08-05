"""Component tests for v2 Session terminate endpoint RBAC validation.

Tests that the v2 POST /sessions/terminate endpoint enforces per-session RBAC via
the BulkActionRBACValidator:

- Regular users can terminate their own sessions (owner permission via scope chain)
- Regular users are denied on other users' sessions (403)
- Superadmin bypasses RBAC and can terminate any session
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.session.request import TerminateSessionsInput
from ai.backend.common.types import SessionId
from ai.backend.manager.views.sokovan.session import MarkTerminatingResult

if TYPE_CHECKING:
    from .conftest import SessionSeedData


@pytest.fixture()
def stub_mark_terminating(scheduling_controller_mock: AsyncMock) -> AsyncMock:
    """Stub `mark_sessions_for_termination` to echo the requested session IDs back
    as `terminating_sessions`. RBAC validation runs *before* the service is called,
    so denied requests never reach this stub.
    """

    async def _mark(
        session_ids: Iterable[SessionId], reason: str, forced: bool
    ) -> MarkTerminatingResult:
        return MarkTerminatingResult(
            cancelled_sessions=[],
            terminating_sessions=list(session_ids),
            force_terminated_sessions=[],
            skipped_sessions=[],
        )

    scheduling_controller_mock.mark_sessions_for_termination.side_effect = _mark
    return scheduling_controller_mock


class TestSessionTerminateV2RBAC:
    """RBAC validation for v2 POST /sessions/terminate.

    The terminate endpoint uses BulkActionProcessor with BulkActionRBACValidator.
    Superadmin bypasses RBAC; regular users can terminate sessions they own (via
    owner permission in user scope) and are denied on other users' sessions.
    Any denial fails the whole bulk request.
    """

    async def test_regular_user_terminating_own_session_succeeds(
        self,
        user_v2_registry: V2ClientRegistry,
        user_session_seed: SessionSeedData,
        stub_mark_terminating: AsyncMock,
    ) -> None:
        """Regular user with owner permission can terminate their own session."""
        result = await user_v2_registry.session.terminate(
            TerminateSessionsInput(session_ids=[user_session_seed.session_id])
        )
        assert user_session_seed.session_id in result.terminating

    async def test_regular_user_terminating_other_users_session_gets_403(
        self,
        user_v2_registry: V2ClientRegistry,
        admin_session_seed: SessionSeedData,
        stub_mark_terminating: AsyncMock,
    ) -> None:
        """Regular user cannot terminate another user's session."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.session.terminate(
                TerminateSessionsInput(session_ids=[admin_session_seed.session_id])
            )

    async def test_superadmin_terminating_other_users_session_bypasses_rbac(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_session_seed: SessionSeedData,
        stub_mark_terminating: AsyncMock,
    ) -> None:
        """Superadmin bypasses RBAC and can terminate other users' sessions."""
        result = await admin_v2_registry.session.terminate(
            TerminateSessionsInput(session_ids=[user_session_seed.session_id])
        )
        assert user_session_seed.session_id in result.terminating
