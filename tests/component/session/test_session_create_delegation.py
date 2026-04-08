"""Component test for delegated session creation via ``owner_access_key``.

Regression coverage for BA-5608: when an admin POSTs to ``/session`` with
``owner_access_key`` set to a regular user's access key, the resulting
``UserScope`` passed to ``AgentRegistry.create_session`` MUST carry the
owner's identity (uuid + role + group_id), not the requester admin's.

The unit test in ``tests/unit/manager/services/session/`` mocks the
repository to verify the wiring inside ``SessionService``. This test
exercises the same invariant end-to-end through the real HTTP layer
(legacy v1 ``POST /session``), real auth (HMAC), real ``query_userinfo``
against the database, and real scope resolution — only the agent RPC and
the image catalog lookup are mocked, since they require external systems
(agent processes, image registry).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine
from yarl import URL

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.types import UserScope

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


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
    def patched_resolve_image(
        self,
        monkeypatch: pytest.MonkeyPatch,
        stub_image_row: MagicMock,
    ) -> AsyncMock:
        """Patch ``SessionRepository.resolve_image`` to return a stub row."""
        mock = AsyncMock(return_value=stub_image_row)
        monkeypatch.setattr(SessionRepository, "resolve_image", mock)
        return mock

    @pytest.fixture()
    def stub_create_session_response(
        self,
        agent_registry: AgentRegistry,
    ) -> AsyncMock:
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
        # which exposes attribute access for ``create_session`` automatically.
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
        server: ServerInfo,
        domain_fixture: str,
        group_name_for_fixture: str,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
        patched_resolve_image: AsyncMock,
        stub_create_session_response: AsyncMock,
    ) -> None:
        """
        POST /session with ``owner_access_key=<regular user's access key>``
        signed by the admin keypair must reach
        ``AgentRegistry.create_session`` with a ``UserScope`` carrying the
        regular user's uuid — not the admin's.
        """
        rel_url = "/session"
        method = "POST"
        body = {
            "session_name": "deleg-session-component",
            "image": "python:latest",
            "architecture": "x86_64",
            "domain": domain_fixture,
            "group": group_name_for_fixture,
            "owner_access_key": regular_user_fixture.keypair.access_key,
            "config": {},
            # ``reuse=False`` skips the existing-session lookup branch in
            # ``AgentRegistry.create_session``; the real path is the new
            # session creation, which is what we want to exercise.
            "reuse": False,
            "enqueue_only": True,
        }

        auth = HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        )
        endpoint = URL(server.url)
        request_date = datetime.now(tzutc())
        signed_headers = auth.sign(
            method=method,
            version="v9.20250722",
            endpoint=endpoint,
            date=request_date,
            rel_url=rel_url,
            content_type="application/json",
        )
        headers = {
            "Content-Type": "application/json",
            "X-BackendAI-Version": "v9.20250722",
            "Date": request_date.isoformat(),
            **signed_headers,
        }

        async with aiohttp.ClientSession() as http:
            resp = await http.post(
                f"{server.url}{rel_url}",
                json=body,
                headers=headers,
            )
            resp_text = await resp.text()

        assert resp.status == 201, f"expected 201 Created, got {resp.status}: {resp_text}"

        # ``patched_resolve_image`` confirms we reached the image lookup,
        # i.e. query_userinfo + scope resolution succeeded for the admin
        # acting on behalf of the regular user.
        patched_resolve_image.assert_awaited()

        # Core invariant: AgentRegistry.create_session received the owner's
        # identity in the UserScope, not the admin's.
        stub_create_session_response.assert_awaited_once()
        call_args = stub_create_session_response.call_args
        # Service calls: create_session(name, image_ref, UserScope(...), owner_access_key, ...)
        passed_user_scope: Any = call_args.args[2]
        passed_owner_access_key: Any = call_args.args[3]

        assert isinstance(passed_user_scope, UserScope)
        assert passed_user_scope.user_uuid == regular_user_fixture.user_uuid, (
            "UserScope.user_uuid must be the owner's UUID, not the requester admin's"
        )
        assert passed_user_scope.user_uuid != admin_user_fixture.user_uuid
        assert passed_owner_access_key == regular_user_fixture.keypair.access_key
