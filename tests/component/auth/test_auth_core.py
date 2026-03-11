from __future__ import annotations

import secrets
from datetime import timedelta

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import AuthenticationError, InvalidRequestError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import AuthorizeRequest, SignupRequest
from ai.backend.common.dto.manager.auth.response import AuthorizeResponse, SignupResponse
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users

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


class TestSignup:
    async def test_signup_returns_credentials(
        self,
        admin_registry: BackendAIClientRegistry,
        db_engine: SAEngine,
        domain_fixture: str,
    ) -> None:
        unique_id = secrets.token_hex(4)
        email = f"signup-test-{unique_id}@test.local"
        password = f"TestP@ss{unique_id}"
        result = await admin_registry.auth.signup(
            SignupRequest(
                domain=domain_fixture,
                email=email,
                password=password,
            ),
        )
        try:
            assert isinstance(result, SignupResponse)
            assert result.access_key != ""
            assert result.secret_key != ""
        finally:
            # Clean up the created user, keypair, and group association.
            async with db_engine.begin() as conn:
                user_row = (
                    await conn.execute(sa.select(users.c.uuid).where(users.c.email == email))
                ).first()
                if user_row:
                    user_uuid = str(user_row.uuid)
                    await conn.execute(
                        association_groups_users.delete().where(
                            association_groups_users.c.user_id == user_uuid
                        )
                    )
                await conn.execute(keypairs.delete().where(keypairs.c.user_id == email))
                await conn.execute(users.delete().where(users.c.email == email))

    async def test_duplicate_email_returns_400(
        self,
        admin_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        with pytest.raises(InvalidRequestError):
            await admin_registry.auth.signup(
                SignupRequest(
                    domain=auth_user_fixture.domain_name,
                    email=auth_user_fixture.email,
                    password="AnyP@ssw0rd123",
                ),
            )
