from __future__ import annotations

import secrets
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import AuthenticationError, InvalidRequestError
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
    async def test_admin_gets_superadmin_role(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.get_role(GetRoleRequest())
        assert isinstance(result, GetRoleResponse)
        assert result.global_role == "superadmin"
        assert result.domain_role == "admin"

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
    async def test_get_ssh_keypair_initially_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.get_ssh_keypair()
        assert isinstance(result, GetSSHKeypairResponse)
        assert result.ssh_public_key == ""

    async def test_generate_ssh_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.auth.generate_ssh_keypair()
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key != ""
        assert result.ssh_private_key != ""

    async def test_upload_ssh_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        privkey = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode()
        pubkey = (
            private_key.public_key()
            .public_bytes(
                serialization.Encoding.OpenSSH,
                serialization.PublicFormat.OpenSSH,
            )
            .decode()
            .strip()
        )
        result = await admin_registry.auth.upload_ssh_keypair(
            UploadSSHKeypairRequest(pubkey=pubkey, privkey=privkey),
        )
        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key.strip() == pubkey
        assert result.ssh_private_key == privkey

        # Verify via get that the public key was stored
        get_result = await admin_registry.auth.get_ssh_keypair()
        assert get_result.ssh_public_key.strip() == pubkey


class TestUpdateFullName:
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

    async def test_update_password_mismatch(
        self,
        auth_user_registry: BackendAIClientRegistry,
        auth_user_fixture: AuthUserFixtureData,
    ) -> None:
        with pytest.raises(InvalidRequestError):
            await auth_user_registry.auth.update_password(
                UpdatePasswordRequest(
                    old_password=auth_user_fixture.password,
                    new_password="NewP@ssw0rd!",
                    new_password2="MismatchP@ss!",
                ),
            )


class TestAuthorize:
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
    async def test_signup_creates_user_with_keypair(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
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
