"""Component tests for v2 Session GET endpoint RBAC validation.

Tests that the v2 GET /sessions/{id} endpoint enforces RBAC:
- Regular users can GET their own session (owner permission via scope chain)
- Regular users WITHOUT permission are denied on other users' sessions (403)
- Superadmin bypasses RBAC and can access any session
- Superadmin querying nonexistent session gets 404
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from .conftest import SessionSeedData


class TestSessionGetV2RBAC:
    """RBAC validation for v2 GET /sessions/{id}.

    The v2 GET endpoint uses SingleEntityActionProcessor with
    single_entity_rbac_validators. Superadmin bypasses RBAC;
    regular users can access their own sessions via owner permission
    but are denied on other users' sessions.
    """

    async def test_regular_user_querying_own_session_succeeds(
        self,
        user_v2_registry: V2ClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Regular user with owner permission can GET their own session."""
        result = await user_v2_registry.session.get(user_session_seed.session_id)
        assert result.id == user_session_seed.session_id

    async def test_regular_user_querying_other_users_session_gets_403(
        self,
        user_v2_registry: V2ClientRegistry,
        admin_session_seed: SessionSeedData,
    ) -> None:
        """Regular user cannot GET another user's session."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.session.get(admin_session_seed.session_id)

    async def test_superadmin_querying_own_session_bypasses_rbac(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_session_seed: SessionSeedData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET their own session."""
        result = await admin_v2_registry.session.get(admin_session_seed.session_id)
        assert result.id == admin_session_seed.session_id

    async def test_superadmin_querying_other_users_session_bypasses_rbac(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Superadmin bypasses RBAC and can GET other users' sessions."""
        result = await admin_v2_registry.session.get(user_session_seed.session_id)
        assert result.id == user_session_seed.session_id

    async def test_superadmin_querying_nonexistent_session_gets_404(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """Superadmin bypasses RBAC but gets 404 for nonexistent session."""
        with pytest.raises(NotFoundError):
            await admin_v2_registry.session.get(uuid.uuid4())
