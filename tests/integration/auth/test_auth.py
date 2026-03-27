from __future__ import annotations

import secrets

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    SignoutRequest,
    SignupRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users

from .conftest import AuthUserFixtureData


@pytest.mark.integration
class TestSignupAndAuthorizeFlow:
    async def test_signup_then_authorize(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        db_engine: SAEngine,
    ) -> None:
        """Signup a new user -> activate via DB -> authorize -> verify credentials work."""
        unique = secrets.token_hex(4)
        email = f"flow-{unique}@test.local"
        password = f"FlowP@ss{unique}"

        # 1. Signup (creates INACTIVE user with auto-generated keypair)
        signup_result = await admin_registry.auth.signup(
            SignupRequest(
                domain=domain_fixture,
                email=email,
                password=password,
                username=f"flow-{unique}",
                full_name=f"Flow User {unique}",
            ),
        )
        assert signup_result.access_key != ""
        assert signup_result.secret_key != ""

        try:
            # 2. Activate user via DB (signup creates INACTIVE users)
            async with db_engine.begin() as conn:
                await conn.execute(
                    sa.update(users).where(users.c.email == email).values(status=UserStatus.ACTIVE)
                )
                await conn.execute(
                    sa.update(keypairs).where(keypairs.c.user_id == email).values(is_active=True)
                )

            # 3. Authorize with the signup credentials
            auth_result = await admin_registry.auth.authorize(
                AuthorizeRequest(
                    type=AuthTokenType.KEYPAIR,
                    domain=domain_fixture,
                    username=email,
                    password=password,
                ),
            )
            assert auth_result.data.access_key != ""
            assert auth_result.data.secret_key != ""
            assert auth_result.data.role == "user"

        finally:
            # Cleanup
            async with db_engine.begin() as conn:
                await conn.execute(keypairs.delete().where(keypairs.c.user_id == email))
                await conn.execute(users.delete().where(users.c.email == email))


@pytest.mark.integration
class TestSignoutFlow:
    async def test_signout_deactivates_user(
        self,
        auth_user_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
        db_engine: SAEngine,
    ) -> None:
        """Verify signout sets user status to INACTIVE."""
        # Verify user is active before signout
        result = await auth_user_registry.auth.verify_auth(
            VerifyAuthRequest(echo="pre-signout"),
        )
        assert result.authorized == "yes"

        # Signout
        await auth_user_registry.auth.signout(
            SignoutRequest(
                email=auth_user_fixture.email,
                password=auth_user_fixture.password,
            ),
        )

        # Verify user status is INACTIVE via DB
        async with db_engine.begin() as conn:
            row = await conn.execute(
                sa.select(users.c.status).where(users.c.uuid == str(auth_user_fixture.user_uuid))
            )
            status = row.scalar_one()
        assert status == UserStatus.INACTIVE
