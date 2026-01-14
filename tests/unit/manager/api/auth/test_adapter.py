"""
Tests for auth API adapter classes.
Tests conversion from ActionResult objects to Response DTOs.
Also tests pydantic DTO validation for request/response models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignoutRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
)
from ai.backend.common.dto.manager.auth.response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdatePasswordNoAuthResponse,
)
from ai.backend.common.dto.manager.auth.types import AuthResponseType, AuthTokenType
from ai.backend.manager.api.auth.adapter import AuthAdapter
from ai.backend.manager.data.auth.types import AuthorizationResult, SSHKeypair
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.services.auth.actions.authorize import AuthorizeActionResult
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairActionResult,
)
from ai.backend.manager.services.auth.actions.get_role import GetRoleActionResult
from ai.backend.manager.services.auth.actions.get_ssh_keypair import GetSSHKeypairActionResult
from ai.backend.manager.services.auth.actions.signup import SignupActionResult
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthActionResult,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import UploadSSHKeypairActionResult


class TestAuthAdapterConversion:
    """Test cases for AuthAdapter conversion methods."""

    @pytest.fixture
    def adapter(self) -> AuthAdapter:
        return AuthAdapter()

    def test_convert_authorize_result(self, adapter: AuthAdapter) -> None:
        """Test converting AuthorizeActionResult to AuthorizeResponse."""
        user_id = uuid4()
        result = AuthorizeActionResult(
            stream_response=None,
            authorization_result=AuthorizationResult(
                user_id=user_id,
                access_key="TESTKEY123",
                secret_key="TESTSECRET456",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            ),
        )

        resp = adapter.convert_authorize_result(result)

        assert isinstance(resp, AuthorizeResponse)
        assert resp.data.response_type == AuthResponseType.SUCCESS
        assert resp.data.access_key == "TESTKEY123"
        assert resp.data.secret_key == "TESTSECRET456"
        assert resp.data.role == UserRole.USER
        assert resp.data.status == UserStatus.ACTIVE

    def test_convert_authorize_result_raises_when_missing(self, adapter: AuthAdapter) -> None:
        """Test that AuthorizationFailed is raised when authorization_result is None."""
        result = AuthorizeActionResult(
            stream_response=None,
            authorization_result=None,
        )

        with pytest.raises(AuthorizationFailed, match="authorization_result is required"):
            adapter.convert_authorize_result(result)

    def test_convert_get_role_result(self, adapter: AuthAdapter) -> None:
        """Test converting GetRoleActionResult to GetRoleResponse."""
        result = GetRoleActionResult(
            global_role="superadmin",
            domain_role="admin",
            group_role="manager",
        )

        resp = adapter.convert_get_role_result(result)

        assert isinstance(resp, GetRoleResponse)
        assert resp.global_role == "superadmin"
        assert resp.domain_role == "admin"
        assert resp.group_role == "manager"

    def test_convert_get_role_result_with_none_group_role(self, adapter: AuthAdapter) -> None:
        """Test converting GetRoleActionResult when group_role is None."""
        result = GetRoleActionResult(
            global_role="user",
            domain_role="user",
            group_role=None,
        )

        resp = adapter.convert_get_role_result(result)

        assert isinstance(resp, GetRoleResponse)
        assert resp.global_role == "user"
        assert resp.domain_role == "user"
        assert resp.group_role is None

    def test_convert_signup_result(self, adapter: AuthAdapter) -> None:
        """Test converting SignupActionResult to SignupResponse."""
        user_id = uuid4()
        result = SignupActionResult(
            user_id=user_id,
            access_key="NEWKEY789",
            secret_key="NEWSECRET012",
        )

        resp = adapter.convert_signup_result(result)

        assert isinstance(resp, SignupResponse)
        assert resp.access_key == "NEWKEY789"
        assert resp.secret_key == "NEWSECRET012"

    def test_convert_update_password_no_auth_result(self, adapter: AuthAdapter) -> None:
        """Test converting UpdatePasswordNoAuthActionResult to UpdatePasswordNoAuthResponse."""
        now = datetime.now(tz=UTC)
        user_id = uuid4()
        result = UpdatePasswordNoAuthActionResult(
            user_id=user_id,
            password_changed_at=now,
        )

        resp = adapter.convert_update_password_no_auth_result(result)

        assert isinstance(resp, UpdatePasswordNoAuthResponse)
        assert resp.password_changed_at == now

    def test_convert_get_ssh_keypair_result(self, adapter: AuthAdapter) -> None:
        """Test converting GetSSHKeypairActionResult to GetSSHKeypairResponse."""
        public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host\n"
        result = GetSSHKeypairActionResult(
            public_key=public_key,
        )

        resp = adapter.convert_get_ssh_keypair_result(result)

        assert isinstance(resp, GetSSHKeypairResponse)
        assert resp.ssh_public_key == public_key

    def test_convert_generate_ssh_keypair_result(self, adapter: AuthAdapter) -> None:
        """Test converting GenerateSSHKeypairActionResult to SSHKeypairResponse."""
        public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host\n"
        private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIG4...\n-----END RSA PRIVATE KEY-----\n"
        result = GenerateSSHKeypairActionResult(
            ssh_keypair=SSHKeypair(
                ssh_public_key=public_key,
                ssh_private_key=private_key,
            ),
        )

        resp = adapter.convert_generate_ssh_keypair_result(result)

        assert isinstance(resp, SSHKeypairResponse)
        assert resp.ssh_public_key == public_key
        assert resp.ssh_private_key == private_key

    def test_convert_upload_ssh_keypair_result(self, adapter: AuthAdapter) -> None:
        """Test converting UploadSSHKeypairActionResult to SSHKeypairResponse."""
        public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host\n"
        private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIG4...\n-----END RSA PRIVATE KEY-----\n"
        result = UploadSSHKeypairActionResult(
            ssh_keypair=SSHKeypair(
                ssh_public_key=public_key,
                ssh_private_key=private_key,
            ),
        )

        resp = adapter.convert_upload_ssh_keypair_result(result)

        assert isinstance(resp, SSHKeypairResponse)
        assert resp.ssh_public_key == public_key
        assert resp.ssh_private_key == private_key


class TestAuthRequestDTOValidation:
    """Test cases for auth request DTO pydantic validation."""

    def test_authorize_request_valid(self) -> None:
        """Test valid AuthorizeRequest parsing."""
        req = AuthorizeRequest(
            type=AuthTokenType.KEYPAIR,
            domain="default",
            username="user@example.com",
            password="password123",
        )
        assert req.type == AuthTokenType.KEYPAIR
        assert req.domain == "default"
        assert req.username == "user@example.com"
        assert req.password == "password123"
        assert req.stoken is None

    def test_authorize_request_with_stoken(self) -> None:
        """Test AuthorizeRequest with optional stoken."""
        req = AuthorizeRequest(
            type=AuthTokenType.JWT,
            domain="default",
            username="user@example.com",
            password="password123",
            stoken="session-token",
        )
        assert req.stoken == "session-token"

    def test_authorize_request_missing_required_field(self) -> None:
        """Test AuthorizeRequest raises error on missing required field."""
        with pytest.raises(ValidationError):
            AuthorizeRequest(
                type=AuthTokenType.KEYPAIR,
                domain="default",
                # missing username and password
            )  # type: ignore[call-arg]

    def test_get_role_request_valid(self) -> None:
        """Test valid GetRoleRequest parsing."""
        group_id = uuid4()
        req = GetRoleRequest(group=group_id)
        assert req.group == group_id

    def test_get_role_request_optional_group(self) -> None:
        """Test GetRoleRequest with optional group."""
        req = GetRoleRequest()
        assert req.group is None

    def test_get_role_request_from_string_uuid(self) -> None:
        """Test GetRoleRequest parses string UUID."""
        group_id = uuid4()
        req = GetRoleRequest(group=str(group_id))  # type: ignore[arg-type]
        assert req.group == group_id

    def test_signup_request_valid(self) -> None:
        """Test valid SignupRequest parsing."""
        req = SignupRequest(
            domain="default",
            email="newuser@example.com",
            password="securepassword",
        )
        assert req.domain == "default"
        assert req.email == "newuser@example.com"
        assert req.password == "securepassword"
        assert req.username is None
        assert req.full_name is None
        assert req.description is None

    def test_signup_request_with_optional_fields(self) -> None:
        """Test SignupRequest with all optional fields."""
        req = SignupRequest(
            domain="default",
            email="newuser@example.com",
            password="securepassword",
            username="newuser",
            full_name="New User",
            description="A new user",
        )
        assert req.username == "newuser"
        assert req.full_name == "New User"
        assert req.description == "A new user"

    def test_signout_request_with_email(self) -> None:
        """Test SignoutRequest with email."""
        req = SignoutRequest(email="user@example.com", password="password")
        assert req.email == "user@example.com"
        assert req.password == "password"

    def test_signout_request_with_username_as_email(self) -> None:
        """Test SignoutRequest uses username as email when email is not provided."""
        req = SignoutRequest(username="user@example.com", password="password")
        assert req.email == "user@example.com"

    def test_signout_request_missing_email_and_username(self) -> None:
        """Test SignoutRequest raises error when both email and username are missing."""
        with pytest.raises(ValidationError, match="Either email or username must be provided"):
            SignoutRequest(password="password")

    def test_update_full_name_request_valid(self) -> None:
        """Test valid UpdateFullNameRequest parsing."""
        req = UpdateFullNameRequest(email="user@example.com", full_name="New Name")
        assert req.email == "user@example.com"
        assert req.full_name == "New Name"

    def test_update_password_request_valid(self) -> None:
        """Test valid UpdatePasswordRequest parsing."""
        req = UpdatePasswordRequest(
            old_password="oldpass",
            new_password="newpass",
            new_password2="newpass",
        )
        assert req.old_password == "oldpass"
        assert req.new_password == "newpass"
        assert req.new_password2 == "newpass"

    def test_update_password_no_auth_request_valid(self) -> None:
        """Test valid UpdatePasswordNoAuthRequest parsing."""
        req = UpdatePasswordNoAuthRequest(
            domain="default",
            username="user@example.com",
            current_password="currentpass",
            new_password="newpass",
        )
        assert req.domain == "default"
        assert req.username == "user@example.com"
        assert req.current_password == "currentpass"
        assert req.new_password == "newpass"

    def test_upload_ssh_keypair_request_valid(self) -> None:
        """Test valid UploadSSHKeypairRequest parsing."""
        req = UploadSSHKeypairRequest(
            pubkey="ssh-rsa AAAAB3...",
            privkey="-----BEGIN RSA PRIVATE KEY-----\n...",
        )
        assert req.pubkey == "ssh-rsa AAAAB3..."
        assert req.privkey == "-----BEGIN RSA PRIVATE KEY-----\n..."


class TestAuthResponseDTOValidation:
    """Test cases for auth response DTO pydantic validation."""

    def test_get_role_response_valid(self) -> None:
        """Test valid GetRoleResponse."""
        resp = GetRoleResponse(
            global_role="superadmin",
            domain_role="admin",
            group_role="manager",
        )
        assert resp.global_role == "superadmin"
        assert resp.domain_role == "admin"
        assert resp.group_role == "manager"

    def test_get_role_response_optional_group_role(self) -> None:
        """Test GetRoleResponse with optional group_role."""
        resp = GetRoleResponse(
            global_role="user",
            domain_role="user",
        )
        assert resp.group_role is None

    def test_signup_response_valid(self) -> None:
        """Test valid SignupResponse."""
        resp = SignupResponse(
            access_key="AKTEST123",
            secret_key="SKTEST456",
        )
        assert resp.access_key == "AKTEST123"
        assert resp.secret_key == "SKTEST456"

    def test_ssh_keypair_response_valid(self) -> None:
        """Test valid SSHKeypairResponse."""
        resp = SSHKeypairResponse(
            ssh_public_key="ssh-rsa AAAAB3...",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\n...",
        )
        assert resp.ssh_public_key == "ssh-rsa AAAAB3..."
        assert resp.ssh_private_key == "-----BEGIN RSA PRIVATE KEY-----\n..."

    def test_get_ssh_keypair_response_valid(self) -> None:
        """Test valid GetSSHKeypairResponse (public key only)."""
        resp = GetSSHKeypairResponse(ssh_public_key="ssh-rsa AAAAB3...")
        assert resp.ssh_public_key == "ssh-rsa AAAAB3..."

    def test_update_password_no_auth_response_valid(self) -> None:
        """Test valid UpdatePasswordNoAuthResponse."""
        now = datetime.now(tz=UTC)
        resp = UpdatePasswordNoAuthResponse(password_changed_at=now)
        assert resp.password_changed_at == now

    def test_response_model_dump_json(self) -> None:
        """Test response DTO can be serialized to JSON."""
        resp = SignupResponse(
            access_key="AKTEST123",
            secret_key="SKTEST456",
        )
        json_data = resp.model_dump(mode="json")
        assert json_data["access_key"] == "AKTEST123"
        assert json_data["secret_key"] == "SKTEST456"
