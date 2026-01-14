"""
Gold format compatibility tests for trafaret → pydantic migration.

These tests verify that the same JSON input dict can be parsed by both
trafaret schemas and pydantic DTOs, ensuring backward compatibility.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import trafaret as t

from ai.backend.common import validators as tx
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
from ai.backend.common.dto.manager.auth.types import AuthTokenType


class TestAuthorizeGoldFormat:
    """Test authorize endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py
    trafaret_schema = t.Dict({
        t.Key("type"): t.Enum("keypair", "jwt"),
        t.Key("domain"): t.String,
        t.Key("username"): t.String,
        t.Key("password"): t.String,
    }).allow_extra("*")

    @pytest.fixture
    def gold_format_keypair(self) -> dict:
        """Gold format JSON for keypair authorization."""
        return {
            "type": "keypair",
            "domain": "default",
            "username": "user@example.com",
            "password": "password123",
        }

    @pytest.fixture
    def gold_format_jwt_with_stoken(self) -> dict:
        """Gold format JSON for JWT authorization with session token."""
        return {
            "type": "jwt",
            "domain": "test-domain",
            "username": "test@example.com",
            "password": "jwtpass",
            "stoken": "session-token-value",
        }

    @pytest.fixture
    def gold_format_with_stoken_camelcase(self) -> dict:
        """Gold format JSON with sToken (camelCase) - legacy format."""
        return {
            "type": "jwt",
            "domain": "default",
            "username": "user@example.com",
            "password": "password123",
            "sToken": "camel-case-token",
        }

    def test_trafaret_parses_keypair(self, gold_format_keypair: dict) -> None:
        """Verify trafaret can parse keypair authorization."""
        result = self.trafaret_schema.check(gold_format_keypair)
        assert result["type"] == "keypair"
        assert result["domain"] == "default"
        assert result["username"] == "user@example.com"
        assert result["password"] == "password123"

    def test_pydantic_parses_keypair(self, gold_format_keypair: dict) -> None:
        """Verify pydantic can parse keypair authorization."""
        result = AuthorizeRequest.model_validate(gold_format_keypair)
        assert result.type == AuthTokenType.KEYPAIR
        assert result.domain == "default"
        assert result.username == "user@example.com"
        assert result.password == "password123"
        assert result.stoken is None

    def test_trafaret_parses_jwt_with_stoken(self, gold_format_jwt_with_stoken: dict) -> None:
        """Verify trafaret can parse JWT authorization with stoken."""
        result = self.trafaret_schema.check(gold_format_jwt_with_stoken)
        assert result["type"] == "jwt"
        assert result["domain"] == "test-domain"
        assert result["username"] == "test@example.com"
        assert result["password"] == "jwtpass"
        # stoken is passed through allow_extra("*")
        assert result.get("stoken") == "session-token-value"

    def test_pydantic_parses_jwt_with_stoken(self, gold_format_jwt_with_stoken: dict) -> None:
        """Verify pydantic can parse JWT authorization with stoken."""
        result = AuthorizeRequest.model_validate(gold_format_jwt_with_stoken)
        assert result.type == AuthTokenType.JWT
        assert result.domain == "test-domain"
        assert result.username == "test@example.com"
        assert result.password == "jwtpass"
        assert result.stoken == "session-token-value"

    def test_trafaret_parses_stoken_camelcase(
        self, gold_format_with_stoken_camelcase: dict
    ) -> None:
        """Verify trafaret can parse sToken (camelCase) via allow_extra."""
        result = self.trafaret_schema.check(gold_format_with_stoken_camelcase)
        assert result["type"] == "jwt"
        # sToken is passed through allow_extra("*")
        assert result.get("sToken") == "camel-case-token"

    def test_pydantic_parses_stoken_camelcase(
        self, gold_format_with_stoken_camelcase: dict
    ) -> None:
        """Verify pydantic can parse sToken (camelCase) legacy format."""
        result = AuthorizeRequest.model_validate(gold_format_with_stoken_camelcase)
        assert result.type == AuthTokenType.JWT
        # pydantic normalizes sToken to stoken field
        assert result.stoken == "camel-case-token"


class TestGetRoleGoldFormat:
    """Test get_role endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py
    trafaret_schema = t.Dict({
        t.Key("group", default=None): t.Null | tx.UUID,
    })

    @pytest.fixture
    def gold_format_with_group(self) -> dict:
        """Gold format JSON with group ID."""
        return {"group": str(uuid4())}

    @pytest.fixture
    def gold_format_without_group(self) -> dict:
        """Gold format JSON without group ID."""
        return {}

    @pytest.fixture
    def gold_format_null_group(self) -> dict:
        """Gold format JSON with explicit null group."""
        return {"group": None}

    def test_trafaret_parses_with_group(self, gold_format_with_group: dict) -> None:
        """Verify trafaret can parse with group ID."""
        result = self.trafaret_schema.check(gold_format_with_group)
        assert result["group"] is not None

    def test_pydantic_parses_with_group(self, gold_format_with_group: dict) -> None:
        """Verify pydantic can parse with group ID."""
        result = GetRoleRequest.model_validate(gold_format_with_group)
        assert result.group is not None

    def test_trafaret_parses_without_group(self, gold_format_without_group: dict) -> None:
        """Verify trafaret can parse without group ID (default None)."""
        result = self.trafaret_schema.check(gold_format_without_group)
        assert result["group"] is None

    def test_pydantic_parses_without_group(self, gold_format_without_group: dict) -> None:
        """Verify pydantic can parse without group ID (default None)."""
        result = GetRoleRequest.model_validate(gold_format_without_group)
        assert result.group is None

    def test_trafaret_parses_null_group(self, gold_format_null_group: dict) -> None:
        """Verify trafaret can parse explicit null group."""
        result = self.trafaret_schema.check(gold_format_null_group)
        assert result["group"] is None

    def test_pydantic_parses_null_group(self, gold_format_null_group: dict) -> None:
        """Verify pydantic can parse explicit null group."""
        result = GetRoleRequest.model_validate(gold_format_null_group)
        assert result.group is None


class TestSignupGoldFormat:
    """Test signup endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py
    trafaret_schema = t.Dict({
        t.Key("domain"): t.String,
        t.Key("email"): t.String,
        t.Key("password"): t.String,
    }).allow_extra("*")

    @pytest.fixture
    def gold_format_minimal(self) -> dict:
        """Gold format JSON with required fields only."""
        return {
            "domain": "default",
            "email": "newuser@example.com",
            "password": "securepassword",
        }

    @pytest.fixture
    def gold_format_full(self) -> dict:
        """Gold format JSON with all optional fields."""
        return {
            "domain": "default",
            "email": "newuser@example.com",
            "password": "securepassword",
            "username": "newuser",
            "full_name": "New User",
            "description": "A new user account",
        }

    @pytest.fixture
    def gold_format_partial_optional(self) -> dict:
        """Gold format JSON with some optional fields."""
        return {
            "domain": "default",
            "email": "newuser@example.com",
            "password": "securepassword",
            "full_name": "New User",
            # username and description omitted
        }

    def test_trafaret_parses_minimal(self, gold_format_minimal: dict) -> None:
        """Verify trafaret can parse minimal signup."""
        result = self.trafaret_schema.check(gold_format_minimal)
        assert result["domain"] == "default"
        assert result["email"] == "newuser@example.com"
        assert result["password"] == "securepassword"

    def test_pydantic_parses_minimal(self, gold_format_minimal: dict) -> None:
        """Verify pydantic can parse minimal signup."""
        result = SignupRequest.model_validate(gold_format_minimal)
        assert result.domain == "default"
        assert result.email == "newuser@example.com"
        assert result.password == "securepassword"
        assert result.username is None
        assert result.full_name is None
        assert result.description is None

    def test_trafaret_parses_full(self, gold_format_full: dict) -> None:
        """Verify trafaret can parse full signup with optional fields."""
        result = self.trafaret_schema.check(gold_format_full)
        assert result["domain"] == "default"
        assert result["email"] == "newuser@example.com"
        assert result["password"] == "securepassword"
        # Optional fields passed through allow_extra("*")
        assert result.get("username") == "newuser"
        assert result.get("full_name") == "New User"
        assert result.get("description") == "A new user account"

    def test_pydantic_parses_full(self, gold_format_full: dict) -> None:
        """Verify pydantic can parse full signup with optional fields."""
        result = SignupRequest.model_validate(gold_format_full)
        assert result.domain == "default"
        assert result.email == "newuser@example.com"
        assert result.password == "securepassword"
        assert result.username == "newuser"
        assert result.full_name == "New User"
        assert result.description == "A new user account"

    def test_trafaret_parses_partial_optional(self, gold_format_partial_optional: dict) -> None:
        """Verify trafaret can parse signup with some optional fields."""
        result = self.trafaret_schema.check(gold_format_partial_optional)
        assert result["domain"] == "default"
        assert result["email"] == "newuser@example.com"
        assert result.get("full_name") == "New User"
        assert result.get("username") is None
        assert result.get("description") is None

    def test_pydantic_parses_partial_optional(self, gold_format_partial_optional: dict) -> None:
        """Verify pydantic can parse signup with some optional fields."""
        result = SignupRequest.model_validate(gold_format_partial_optional)
        assert result.domain == "default"
        assert result.email == "newuser@example.com"
        assert result.full_name == "New User"
        assert result.username is None
        assert result.description is None


class TestSignoutGoldFormat:
    """Test signout endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py - uses AliasedKey
    trafaret_schema = t.Dict({
        tx.AliasedKey(["email", "username"]): t.String,
        t.Key("password"): t.String,
    })

    @pytest.fixture
    def gold_format_with_email(self) -> dict:
        """Gold format JSON with email field."""
        return {
            "email": "user@example.com",
            "password": "password123",
        }

    @pytest.fixture
    def gold_format_with_username(self) -> dict:
        """Gold format JSON with username field (alias for email)."""
        return {
            "username": "user@example.com",
            "password": "password123",
        }

    def test_trafaret_parses_with_email(self, gold_format_with_email: dict) -> None:
        """Verify trafaret can parse with email field."""
        result = self.trafaret_schema.check(gold_format_with_email)
        assert result["email"] == "user@example.com"
        assert result["password"] == "password123"

    def test_pydantic_parses_with_email(self, gold_format_with_email: dict) -> None:
        """Verify pydantic can parse with email field."""
        result = SignoutRequest.model_validate(gold_format_with_email)
        assert result.email == "user@example.com"
        assert result.password == "password123"

    def test_trafaret_parses_with_username(self, gold_format_with_username: dict) -> None:
        """Verify trafaret can parse with username field (alias)."""
        result = self.trafaret_schema.check(gold_format_with_username)
        # AliasedKey normalizes to first key name
        assert result["email"] == "user@example.com"
        assert result["password"] == "password123"

    def test_pydantic_parses_with_username(self, gold_format_with_username: dict) -> None:
        """Verify pydantic can parse with username field (alias)."""
        result = SignoutRequest.model_validate(gold_format_with_username)
        # model_validator normalizes username to email
        assert result.email == "user@example.com"
        assert result.password == "password123"


class TestUpdateFullNameGoldFormat:
    """Test update_full_name endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py
    trafaret_schema = t.Dict({
        t.Key("email"): t.String,
        t.Key("full_name"): t.String,
    })

    @pytest.fixture
    def gold_format(self) -> dict:
        """Gold format JSON for update full name."""
        return {
            "email": "user@example.com",
            "full_name": "Updated Name",
        }

    def test_trafaret_parses(self, gold_format: dict) -> None:
        """Verify trafaret can parse update full name request."""
        result = self.trafaret_schema.check(gold_format)
        assert result["email"] == "user@example.com"
        assert result["full_name"] == "Updated Name"

    def test_pydantic_parses(self, gold_format: dict) -> None:
        """Verify pydantic can parse update full name request."""
        result = UpdateFullNameRequest.model_validate(gold_format)
        assert result.email == "user@example.com"
        assert result.full_name == "Updated Name"


class TestUpdatePasswordGoldFormat:
    """Test update_password endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py
    trafaret_schema = t.Dict({
        t.Key("old_password"): t.String,
        t.Key("new_password"): t.String,
        t.Key("new_password2"): t.String,
    })

    @pytest.fixture
    def gold_format(self) -> dict:
        """Gold format JSON for update password."""
        return {
            "old_password": "oldpass123",
            "new_password": "newpass456",
            "new_password2": "newpass456",
        }

    def test_trafaret_parses(self, gold_format: dict) -> None:
        """Verify trafaret can parse update password request."""
        result = self.trafaret_schema.check(gold_format)
        assert result["old_password"] == "oldpass123"
        assert result["new_password"] == "newpass456"
        assert result["new_password2"] == "newpass456"

    def test_pydantic_parses(self, gold_format: dict) -> None:
        """Verify pydantic can parse update password request."""
        result = UpdatePasswordRequest.model_validate(gold_format)
        assert result.old_password == "oldpass123"
        assert result.new_password == "newpass456"
        assert result.new_password2 == "newpass456"


class TestUpdatePasswordNoAuthGoldFormat:
    """Test update_password_no_auth endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py
    trafaret_schema = t.Dict({
        t.Key("domain"): t.String,
        t.Key("username"): t.String,
        t.Key("current_password"): t.String,
        t.Key("new_password"): t.String,
    })

    @pytest.fixture
    def gold_format(self) -> dict:
        """Gold format JSON for update password without auth."""
        return {
            "domain": "default",
            "username": "user@example.com",
            "current_password": "currentpass",
            "new_password": "newpass456",
        }

    def test_trafaret_parses(self, gold_format: dict) -> None:
        """Verify trafaret can parse update password no auth request."""
        result = self.trafaret_schema.check(gold_format)
        assert result["domain"] == "default"
        assert result["username"] == "user@example.com"
        assert result["current_password"] == "currentpass"
        assert result["new_password"] == "newpass456"

    def test_pydantic_parses(self, gold_format: dict) -> None:
        """Verify pydantic can parse update password no auth request."""
        result = UpdatePasswordNoAuthRequest.model_validate(gold_format)
        assert result.domain == "default"
        assert result.username == "user@example.com"
        assert result.current_password == "currentpass"
        assert result.new_password == "newpass456"


class TestUploadSSHKeypairGoldFormat:
    """Test upload_ssh_keypair endpoint JSON format compatibility."""

    # Trafaret schema from original auth.py
    trafaret_schema = t.Dict({
        t.Key("pubkey"): t.String,
        t.Key("privkey"): t.String,
    })

    @pytest.fixture
    def gold_format(self) -> dict:
        """Gold format JSON for upload SSH keypair."""
        return {
            "pubkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@host",
            "privkey": "-----BEGIN RSA PRIVATE KEY-----\nMIIG4...\n-----END RSA PRIVATE KEY-----",
        }

    def test_trafaret_parses(self, gold_format: dict) -> None:
        """Verify trafaret can parse upload SSH keypair request."""
        result = self.trafaret_schema.check(gold_format)
        assert result["pubkey"].startswith("ssh-rsa")
        assert result["privkey"].startswith("-----BEGIN RSA PRIVATE KEY-----")

    def test_pydantic_parses(self, gold_format: dict) -> None:
        """Verify pydantic can parse upload SSH keypair request."""
        result = UploadSSHKeypairRequest.model_validate(gold_format)
        assert result.pubkey.startswith("ssh-rsa")
        assert result.privkey.startswith("-----BEGIN RSA PRIVATE KEY-----")
