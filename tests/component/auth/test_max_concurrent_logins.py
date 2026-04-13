from __future__ import annotations

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import AuthorizeRequest
from ai.backend.common.dto.manager.auth.response import AuthorizeResponse
from ai.backend.common.dto.manager.auth.types import AuthTokenType

from .conftest import AuthUserFixtureData


class TestMaxConcurrentLogins:
    """Test that exceeding max_concurrent_logins returns HTTP 409 Conflict."""

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

        # Assert: second login raises BackendAPIError with HTTP 409
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.auth.authorize(authorize_req)
        assert exc_info.value.status == 409
