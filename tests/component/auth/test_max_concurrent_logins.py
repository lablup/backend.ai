from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import AuthorizeRequest
from ai.backend.common.dto.manager.auth.response import AuthorizeResponse
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow

from .conftest import AuthUserFixtureData


class TestMaxConcurrentLogins:
    """Test that exceeding max_concurrent_logins returns HTTP 409 Conflict."""

    @pytest.fixture()
    async def max_concurrent_logins_limit(
        self,
        db_engine: SAEngine,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        """Set max_concurrent_logins=1 for the auth user's resource policy."""
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(UserResourcePolicyRow.__table__)
                .where(
                    UserResourcePolicyRow.__table__.c.name
                    == sa.select(sa.text("resource_policy"))
                    .select_from(sa.text("users"))
                    .where(sa.text(f"uuid = '{auth_user_fixture.user_uuid}'"))
                    .scalar_subquery()
                )
                .values(max_concurrent_logins=1)
            )

    async def test_second_login_rejected_when_at_limit(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
        max_concurrent_logins_limit: None,
    ) -> None:
        authorize_req = AuthorizeRequest(
            type=AuthTokenType.KEYPAIR,
            domain=auth_user_fixture.domain_name,
            username=auth_user_fixture.email,
            password=auth_user_fixture.password,
        )

        # Act: first login succeeds
        result = await admin_registry.auth.authorize(authorize_req)
        assert isinstance(result, AuthorizeResponse)

        # Assert: second login raises BackendAPIError with HTTP 409 and correct error type
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.auth.authorize(authorize_req)
        assert exc_info.value.status == 409
        assert exc_info.value.data["type"].split("/")[-1] == "active-login-session-exists"
