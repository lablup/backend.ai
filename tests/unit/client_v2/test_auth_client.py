from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.auth import AuthClient
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignoutRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
    VerifyAuthRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignoutResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdateFullNameResponse,
    UpdatePasswordNoAuthResponse,
    UpdatePasswordResponse,
    VerifyAuthResponse,
)
from ai.backend.common.dto.manager.auth.types import AuthResponseType, AuthTokenType

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_client(
    mock_session: MagicMock | None = None,
    config: ClientConfig | None = None,
) -> BackendAIClient:
    return BackendAIClient(
        config or _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock session whose ``request()`` returns *resp* as a context manager."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


class TestAuthClient:
    @pytest.mark.asyncio
    async def test_authorize(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "data": {
                    "response_type": AuthResponseType.SUCCESS,
                    "access_key": "AKTEST",
                    "secret_key": "sktest",
                    "role": "admin",
                    "status": "active",
                    "type": AuthTokenType.KEYPAIR,
                },
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = AuthorizeRequest(
            type=AuthTokenType.KEYPAIR,
            domain="default",
            username="user@example.com",
            password="secret",
        )
        result = await auth_client.authorize(request)

        assert isinstance(result, AuthorizeResponse)
        assert result.data.access_key == "AKTEST"
        assert result.data.secret_key == "sktest"
        assert result.data.role == "admin"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/authorize" in str(call_args.args[1])
        assert call_args.kwargs["json"]["type"] == "keypair"
        assert call_args.kwargs["json"]["domain"] == "default"

    @pytest.mark.asyncio
    async def test_signup(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "access_key": "AKnew",
                "secret_key": "sknew",
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = SignupRequest(
            domain="default",
            email="new@example.com",
            password="newpass",
            username="newuser",
        )
        result = await auth_client.signup(request)

        assert isinstance(result, SignupResponse)
        assert result.access_key == "AKnew"
        assert result.secret_key == "sknew"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/signup" in str(call_args.args[1])
        assert call_args.kwargs["json"]["email"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_signout(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = SignoutRequest(email="user@example.com", password="secret")
        result = await auth_client.signout(request)

        assert isinstance(result, SignoutResponse)

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/signout" in str(call_args.args[1])
        assert call_args.kwargs["json"]["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_role(self) -> None:
        group_id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "global_role": "superadmin",
                "domain_role": "admin",
                "group_role": "admin",
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = GetRoleRequest(group=group_id)
        result = await auth_client.get_role(request)

        assert isinstance(result, GetRoleResponse)
        assert result.global_role == "superadmin"
        assert result.domain_role == "admin"
        assert result.group_role == "admin"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/auth/role" in str(call_args.args[1])
        assert call_args.kwargs["params"] == {"group": str(group_id)}
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_get_role_without_group(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "global_role": "user",
                "domain_role": "user",
                "group_role": None,
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = GetRoleRequest()
        result = await auth_client.get_role(request)

        assert isinstance(result, GetRoleResponse)
        assert result.global_role == "user"
        assert result.group_role is None

        call_args = mock_session.request.call_args
        assert call_args.kwargs["params"] == {}

    @pytest.mark.asyncio
    async def test_update_password(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"error_msg": None})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = UpdatePasswordRequest(
            old_password="old",
            new_password="new",
            new_password2="new",
        )
        result = await auth_client.update_password(request)

        assert isinstance(result, UpdatePasswordResponse)
        assert result.error_msg is None

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/update-password" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_update_password_no_auth(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"password_changed_at": "2025-01-01T00:00:00+00:00"}
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = UpdatePasswordNoAuthRequest(
            domain="default",
            username="user@example.com",
            current_password="expired",
            new_password="fresh",
        )
        result = await auth_client.update_password_no_auth(request)

        assert isinstance(result, UpdatePasswordNoAuthResponse)
        assert result.password_changed_at == "2025-01-01T00:00:00+00:00"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/update-password-no-auth" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_update_full_name(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = UpdateFullNameRequest(
            email="user@example.com",
            full_name="New Name",
        )
        result = await auth_client.update_full_name(request)

        assert isinstance(result, UpdateFullNameResponse)

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/update-full-name" in str(call_args.args[1])
        assert call_args.kwargs["json"]["full_name"] == "New Name"

    @pytest.mark.asyncio
    async def test_get_ssh_keypair(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"ssh_public_key": "ssh-rsa AAAA... user@host"})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        result = await auth_client.get_ssh_keypair()

        assert isinstance(result, GetSSHKeypairResponse)
        assert result.ssh_public_key == "ssh-rsa AAAA... user@host"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/auth/ssh-keypair" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_generate_ssh_keypair(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "ssh_public_key": "ssh-rsa AAAA... generated",
                "ssh_private_key": "-----BEGIN RSA PRIVATE KEY-----\n...",
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        result = await auth_client.generate_ssh_keypair()

        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key == "ssh-rsa AAAA... generated"
        assert "PRIVATE KEY" in result.ssh_private_key

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "PATCH"
        assert "/auth/ssh-keypair" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_upload_ssh_keypair(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "ssh_public_key": "ssh-rsa AAAA... uploaded",
                "ssh_private_key": "-----BEGIN RSA PRIVATE KEY-----\nuploaded",
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = UploadSSHKeypairRequest(
            pubkey="ssh-rsa AAAA... uploaded",
            privkey="-----BEGIN RSA PRIVATE KEY-----\nuploaded",
        )
        result = await auth_client.upload_ssh_keypair(request)

        assert isinstance(result, SSHKeypairResponse)
        assert result.ssh_public_key == "ssh-rsa AAAA... uploaded"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/ssh-keypair" in str(call_args.args[1])
        assert call_args.kwargs["json"]["pubkey"] == "ssh-rsa AAAA... uploaded"

    @pytest.mark.asyncio
    async def test_verify_auth(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "authorized": "yes",
                "echo": "hello",
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        auth_client = AuthClient(client)

        request = VerifyAuthRequest(echo="hello")
        result = await auth_client.verify_auth(request)

        assert isinstance(result, VerifyAuthResponse)
        assert result.authorized == "yes"
        assert result.echo == "hello"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/auth/test" in str(call_args.args[1])
        assert call_args.kwargs["json"]["echo"] == "hello"
