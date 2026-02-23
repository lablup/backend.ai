from __future__ import annotations

import secrets
import uuid

import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import AuthenticationError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdateFullNameResponse,
    UpdatePasswordResponse,
    VerifyAuthResponse,
)
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users

from .conftest import AuthUserFixtureData


class TestVerifyAuth:
    @pytest.mark.asyncio
    async def test_admin_verifies_auth(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.verify_auth(
            VerifyAuthRequest(echo="hello-from-admin"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"
        assert result.echo == "hello-from-admin"

    @pytest.mark.asyncio
    async def test_regular_user_verifies_auth(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.auth.verify_auth(
            VerifyAuthRequest(echo="hello-from-user"),
        )
        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"
        assert result.echo == "hello-from-user"


class TestGetRole:
    @pytest.mark.asyncio
    async def test_admin_gets_superadmin_role(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.get_role(GetRoleRequest())
        assert isinstance(result, GetRoleResponse)
        assert result.global_role == "superadmin"
        assert result.domain_role == "admin"

    @pytest.mark.asyncio
    async def test_regular_user_gets_user_role(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.auth.get_role(GetRoleRequest())
        assert isinstance(result, GetRoleResponse)
        assert result.global_role == "user"
        assert result.domain_role == "user"

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 HMAC signing omits query params from the signature, "
            "but the server verifies against request.raw_path which includes ?group=..."
        ),
    )
    @pytest.mark.asyncio
    async def test_get_role_with_group_xfail(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        result = await admin_registry.auth.get_role(
            GetRoleRequest(group=group_fixture),
        )
        assert isinstance(result, GetRoleResponse)


class TestSSHKeypair:
    @pytest.mark.asyncio
    async def test_get_ssh_keypair_initially_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.get_ssh_keypair()
        assert isinstance(result, GetSSHKeypairResponse)
        assert result.ssh_public_key == ""

    @pytest.mark.asyncio
    async def test_generate_ssh_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.generate_ssh_keypair()
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key != ""
        assert result.ssh_private_key != ""

    @pytest.mark.asyncio
    async def test_upload_ssh_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQDtest test@test"
        privkey = "-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAtest\n-----END RSA PRIVATE KEY-----"
        result = await admin_registry.auth.upload_ssh_keypair(
            UploadSSHKeypairRequest(pubkey=pubkey, privkey=privkey),
        )
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key == pubkey
        assert result.ssh_private_key == privkey

        # Verify via get that the public key was stored
        get_result = await admin_registry.auth.get_ssh_keypair()
        assert get_result.ssh_public_key == pubkey


class TestUpdateFullName:
    @pytest.mark.asyncio
    async def test_admin_updates_full_name(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.update_full_name(
            UpdateFullNameRequest(
                email="ignored@test.local",
                full_name="Updated Admin Name",
            ),
        )
        assert isinstance(result, UpdateFullNameResponse)


class TestUpdatePassword:
    @pytest.mark.asyncio
    async def test_update_password_succeeds(
        self,
        auth_user_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        new_password = f"NewP@ss{secrets.token_hex(4)}"
        result = await auth_user_registry.auth.update_password(
            UpdatePasswordRequest(
                old_password=auth_user_fixture.password,
                new_password=new_password,
                new_password2=new_password,
            ),
        )
        assert isinstance(result, UpdatePasswordResponse)
        assert result.error_msg is None

    @pytest.mark.asyncio
    async def test_update_password_mismatch(
        self,
        auth_user_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        result = await auth_user_registry.auth.update_password(
            UpdatePasswordRequest(
                old_password=auth_user_fixture.password,
                new_password="NewP@ssw0rd!",
                new_password2="MismatchP@ss!",
            ),
        )
        assert isinstance(result, UpdatePasswordResponse)
        assert result.error_msg is not None


class TestAuthorize:
    @pytest.mark.asyncio
    async def test_authorize_with_keypair_type(
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

    @pytest.mark.asyncio
    async def test_authorize_with_wrong_password(
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


class TestSignup:
    @pytest.mark.asyncio
    async def test_signup_creates_user_with_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        db_engine: SAEngine,
    ) -> None:
        unique = secrets.token_hex(4)
        email = f"signup-{unique}@test.local"
        result = await admin_registry.auth.signup(
            SignupRequest(
                domain=domain_fixture,
                email=email,
                password=f"SignupP@ss{unique}",
                username=f"signup-{unique}",
                full_name=f"Signup User {unique}",
            ),
        )
        assert isinstance(result, SignupResponse)
        assert result.access_key != ""
        assert result.secret_key != ""

        # Cleanup: remove the signup-created user and keypair
        async with db_engine.begin() as conn:
            await conn.execute(keypairs.delete().where(keypairs.c.user_id == email))
            await conn.execute(users.delete().where(users.c.email == email))
