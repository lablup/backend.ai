from __future__ import annotations

from datetime import timedelta

import pytest

from ai.backend.client.v2.exceptions import AuthenticationError, InvalidRequestError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import AuthorizeRequest
from ai.backend.common.dto.manager.auth.response import AuthorizeResponse
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.manager.config.provider import ManagerConfigProvider

from .conftest import AuthUserFixtureData


class TestAuthorize:
    async def test_keypair_auth_returns_credentials(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        result = await admin_registry.auth.authorize(
            AuthorizeRequest(
                type=AuthTokenType.KEYPAIR,
                domain=auth_user_fixture.domain_name,
                username=auth_user_fixture.email,
                password=auth_user_fixture.password,
            ),
        )
        assert isinstance(result, AuthorizeResponse)
        assert result.data.access_key != ""
        assert result.data.secret_key != ""
        assert result.data.role == "user"
        assert result.data.status == "active"

    async def test_wrong_password_returns_401(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        with pytest.raises(AuthenticationError):
            await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.KEYPAIR,
                    domain=auth_user_fixture.domain_name,
                    username=auth_user_fixture.email,
                    password="completely-wrong-password",
                ),
            )

    async def test_inactive_user_returns_401(
        self,
        admin_registry: BackendAIClientRegistry,
        inactive_user_fixture: AuthUserFixtureData,
    ) -> None:
        with pytest.raises(AuthenticationError):
            await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.KEYPAIR,
                    domain=inactive_user_fixture.domain_name,
                    username=inactive_user_fixture.email,
                    password=inactive_user_fixture.password,
                ),
            )

    async def test_before_verification_user_returns_401(
        self,
        admin_registry: BackendAIClientRegistry,
        before_verification_user_fixture: AuthUserFixtureData,
    ) -> None:
        with pytest.raises(AuthenticationError):
            await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.KEYPAIR,
                    domain=before_verification_user_fixture.domain_name,
                    username=before_verification_user_fixture.email,
                    password=before_verification_user_fixture.password,
                ),
            )

    async def test_expired_password_returns_401(
        self,
        admin_registry: BackendAIClientRegistry,
        config_provider: ManagerConfigProvider,
        expired_password_user_fixture: AuthUserFixtureData,
    ) -> None:
        original_config = config_provider._config
        new_auth = original_config.auth.model_copy(
            update={"max_password_age": timedelta(seconds=0)},
        )
        config_provider._config = original_config.model_copy(update={"auth": new_auth})
        try:
            with pytest.raises(AuthenticationError):
                await admin_registry.auth.authorize(
                    AuthorizeRequest(
                        type=AuthTokenType.KEYPAIR,
                        domain=expired_password_user_fixture.domain_name,
                        username=expired_password_user_fixture.email,
                        password=expired_password_user_fixture.password,
                    ),
                )
        finally:
            config_provider._config = original_config

    async def test_unsupported_auth_type_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        with pytest.raises(InvalidRequestError):
            await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.JWT,
                    domain=auth_user_fixture.domain_name,
                    username=auth_user_fixture.email,
                    password=auth_user_fixture.password,
                ),
            )
