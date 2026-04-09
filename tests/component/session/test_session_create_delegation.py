"""BA-5608: ``POST /session`` with ``owner_access_key`` must build ``UserScope``
from the owner, not the requester admin."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import CreateFromParamsRequest
from ai.backend.common.types import SessionTypes
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.types import UserScope

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


class TestDelegatedSessionCreation:
    """Tests for legacy ``POST /session`` with ``owner_access_key`` (BA-5608)."""

    @pytest.fixture()
    def stub_image_row(self) -> MagicMock:
        """Fake image row that satisfies ``SessionService.create_from_params``.

        The real ``resolve_image`` would query the ``images`` table; we bypass
        it because seeding a fully-valid ImageRow (with registry, labels,
        architecture) is out of scope for this test.
        """
        image_row = MagicMock()
        image_row.id = uuid.uuid4()
        image_row.image_ref = MagicMock()
        return image_row

    @pytest.fixture()
    def session_repository_with_stub_image(
        self,
        session_repository: SessionRepository,
        stub_image_row: MagicMock,
    ) -> SessionRepository:
        """Stub ``resolve_image`` on the injected ``SessionRepository`` instance."""
        session_repository.resolve_image = AsyncMock(  # type: ignore[method-assign]
            return_value=stub_image_row
        )
        return session_repository

    @pytest.fixture()
    def mock_create_session(self, agent_registry: AgentRegistry) -> AsyncMock:
        """Make the mocked ``AgentRegistry.create_session`` return a successful response."""
        mock = AsyncMock(
            return_value={
                "sessionId": "00000000-0000-0000-0000-000000000001",
                "sessionName": "delegated-session",
                "status": "PENDING",
                "service_ports": [],
                "servicePorts": [],
                "created": True,
            }
        )
        # ``agent_registry`` from the shared fixture is ``AsyncMock(spec=AgentRegistry)``,
        # so attribute assignment is enough — no class-level patching required.
        agent_registry.create_session = mock  # type: ignore[method-assign]
        return mock

    @pytest.fixture()
    async def group_name_for_fixture(
        self,
        db_engine: SAEngine,
        group_fixture: uuid.UUID,
    ) -> str:
        """Resolve the group name corresponding to ``group_fixture`` (a UUID)."""
        async with db_engine.begin() as conn:
            result = await conn.execute(
                sa.select(GroupRow.__table__.c.name).where(GroupRow.__table__.c.id == group_fixture)
            )
            name = result.scalar()
        assert name is not None, "group_fixture row missing name"
        return str(name)

    async def test_admin_create_with_owner_access_key_routes_owner_into_user_scope(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        group_name_for_fixture: str,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
        session_repository_with_stub_image: SessionRepository,
        mock_create_session: AsyncMock,
    ) -> None:
        """
        POST /session signed by the admin keypair, with
        ``owner_access_key=<regular user's access key>``, must reach
        ``AgentRegistry.create_session`` with a ``UserScope`` carrying the
        regular user's uuid — not the admin's.
        """
        request = CreateFromParamsRequest(
            session_name="deleg-session-component",
            image="python:latest",
            architecture="x86_64",
            session_type=SessionTypes.INTERACTIVE,
            domain=domain_fixture,
            group=group_name_for_fixture,
            owner_access_key=regular_user_fixture.keypair.access_key,
            # ``reuse=False`` skips the existing-session lookup branch in
            # ``AgentRegistry.create_session`` so we exercise the new
            # session creation path.
            reuse=False,
            enqueue_only=True,
        )

        # Reuse the v2 client's signed transport for a v1 endpoint
        # (same pattern as ``tests/component/user/test_keypair_ops.py``).
        await admin_registry._client._request(
            "POST",
            "/session",
            json=request.model_dump(mode="json", exclude_none=True),
        )

        # Stubbed ``resolve_image`` having been called confirms we reached the
        # image lookup, i.e. ``query_userinfo`` + scope resolution succeeded
        # for the admin acting on behalf of the regular user.
        session_repository_with_stub_image.resolve_image.assert_awaited()  # type: ignore[attr-defined]

        # Core invariant: ``AgentRegistry.create_session`` received the owner's
        # identity in the ``UserScope``, not the admin's.
        mock_create_session.assert_awaited_once()
        call_args = mock_create_session.call_args
        # Service calls: create_session(name, image_ref, UserScope(...), owner_access_key, ...)
        passed_user_scope: Any = call_args.args[2]
        passed_owner_access_key: Any = call_args.args[3]

        assert isinstance(passed_user_scope, UserScope)
        assert passed_user_scope.user_uuid == regular_user_fixture.user_uuid, (
            "UserScope.user_uuid must be the owner's UUID, not the requester admin's"
        )
        assert passed_user_scope.user_uuid != admin_user_fixture.user_uuid
        assert passed_owner_access_key == regular_user_fixture.keypair.access_key
