"""Tests for ai.backend.common.dto.manager.v2.auth.types module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.auth.types import AuthResponseType, AuthTokenType, TwoFactorType
from ai.backend.common.dto.manager.v2.auth.types import (
    AuthCredentialInfo,
    PasswordChangeInfo,
    RoleInfo,
    SSHKeypairInfo,
    TwoFactorInfo,
)
from ai.backend.common.dto.manager.v2.auth.types import AuthResponseType as ExportedAuthResponseType
from ai.backend.common.dto.manager.v2.auth.types import AuthTokenType as ExportedAuthTokenType
from ai.backend.common.dto.manager.v2.auth.types import TwoFactorType as ExportedTwoFactorType


class TestAuthTokenTypeValues:
    """Tests for AuthTokenType enum values."""

    def test_keypair_value(self) -> None:
        assert AuthTokenType.KEYPAIR.value == "keypair"

    def test_jwt_value(self) -> None:
        assert AuthTokenType.JWT.value == "jwt"

    def test_all_values_are_strings(self) -> None:
        for member in AuthTokenType:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(AuthTokenType)
        assert len(members) == 2

    def test_from_string_keypair(self) -> None:
        assert AuthTokenType("keypair") is AuthTokenType.KEYPAIR

    def test_from_string_jwt(self) -> None:
        assert AuthTokenType("jwt") is AuthTokenType.JWT


class TestAuthResponseTypeValues:
    """Tests for AuthResponseType enum values."""

    def test_success_value(self) -> None:
        assert AuthResponseType.SUCCESS.value == "success"

    def test_require_two_factor_registration_value(self) -> None:
        assert (
            AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION.value
            == "REQUIRE_TWO_FACTOR_REGISTRATION"
        )

    def test_require_two_factor_auth_value(self) -> None:
        assert AuthResponseType.REQUIRE_TWO_FACTOR_AUTH.value == "REQUIRE_TWO_FACTOR_AUTH"

    def test_all_values_are_strings(self) -> None:
        for member in AuthResponseType:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(AuthResponseType)
        assert len(members) == 3


class TestTwoFactorTypeValues:
    """Tests for TwoFactorType enum values."""

    def test_totp_value(self) -> None:
        assert TwoFactorType.TOTP.value == "TOTP"

    def test_all_values_are_strings(self) -> None:
        for member in TwoFactorType:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(TwoFactorType)
        assert len(members) == 1

    def test_from_string_totp(self) -> None:
        assert TwoFactorType("TOTP") is TwoFactorType.TOTP


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported from types module."""

    def test_auth_token_type_is_same_object(self) -> None:
        assert ExportedAuthTokenType is AuthTokenType

    def test_auth_response_type_is_same_object(self) -> None:
        assert ExportedAuthResponseType is AuthResponseType

    def test_two_factor_type_is_same_object(self) -> None:
        assert ExportedTwoFactorType is TwoFactorType

    def test_auth_token_type_keypair_value(self) -> None:
        assert ExportedAuthTokenType.KEYPAIR.value == "keypair"

    def test_auth_token_type_jwt_value(self) -> None:
        assert ExportedAuthTokenType.JWT.value == "jwt"

    def test_auth_response_type_success_value(self) -> None:
        assert ExportedAuthResponseType.SUCCESS.value == "success"

    def test_two_factor_type_totp_value(self) -> None:
        assert ExportedTwoFactorType.TOTP.value == "TOTP"


class TestAuthCredentialInfoCreation:
    """Tests for AuthCredentialInfo Pydantic model creation."""

    def test_basic_creation(self) -> None:
        cred = AuthCredentialInfo(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            role="user",
            status="active",
        )
        assert cred.access_key == "AKIAIOSFODNN7EXAMPLE"
        assert cred.secret_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert cred.role == "user"
        assert cred.status == "active"

    def test_creation_with_superadmin_role(self) -> None:
        cred = AuthCredentialInfo(
            access_key="AKID",
            secret_key="SECRET",
            role="superadmin",
            status="active",
        )
        assert cred.role == "superadmin"

    def test_creation_from_dict(self) -> None:
        cred = AuthCredentialInfo.model_validate({
            "access_key": "AKID",
            "secret_key": "SECRET",
            "role": "user",
            "status": "inactive",
        })
        assert cred.access_key == "AKID"
        assert cred.status == "inactive"


class TestAuthCredentialInfoSerialization:
    """Tests for AuthCredentialInfo serialization and deserialization."""

    def test_model_dump(self) -> None:
        cred = AuthCredentialInfo(
            access_key="AKID",
            secret_key="SECRET",
            role="user",
            status="active",
        )
        data = cred.model_dump()
        assert data["access_key"] == "AKID"
        assert data["secret_key"] == "SECRET"
        assert data["role"] == "user"
        assert data["status"] == "active"

    def test_model_dump_json(self) -> None:
        cred = AuthCredentialInfo(
            access_key="AKID",
            secret_key="SECRET",
            role="user",
            status="active",
        )
        json_str = cred.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["access_key"] == "AKID"
        assert parsed["secret_key"] == "SECRET"

    def test_serialization_round_trip(self) -> None:
        cred = AuthCredentialInfo(
            access_key="AKID",
            secret_key="SECRET",
            role="admin",
            status="active",
        )
        json_str = cred.model_dump_json()
        restored = AuthCredentialInfo.model_validate_json(json_str)
        assert restored.access_key == cred.access_key
        assert restored.secret_key == cred.secret_key
        assert restored.role == cred.role
        assert restored.status == cred.status


class TestTwoFactorInfoCreation:
    """Tests for TwoFactorInfo Pydantic model creation."""

    def test_basic_creation(self) -> None:
        tfi = TwoFactorInfo(
            type=TwoFactorType.TOTP,
            token="abc123token",
        )
        assert tfi.type == TwoFactorType.TOTP
        assert tfi.token == "abc123token"

    def test_creation_from_string_values(self) -> None:
        tfi = TwoFactorInfo.model_validate({
            "type": "TOTP",
            "token": "mytoken",
        })
        assert tfi.type == TwoFactorType.TOTP
        assert tfi.token == "mytoken"


class TestTwoFactorInfoSerialization:
    """Tests for TwoFactorInfo serialization."""

    def test_model_dump_json(self) -> None:
        tfi = TwoFactorInfo(
            type=TwoFactorType.TOTP,
            token="abc123",
        )
        json_str = tfi.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["type"] == "TOTP"
        assert parsed["token"] == "abc123"

    def test_serialization_round_trip(self) -> None:
        tfi = TwoFactorInfo(
            type=TwoFactorType.TOTP,
            token="mytoken",
        )
        json_str = tfi.model_dump_json()
        restored = TwoFactorInfo.model_validate_json(json_str)
        assert restored.type == tfi.type
        assert restored.token == tfi.token


class TestRoleInfoCreation:
    """Tests for RoleInfo Pydantic model creation."""

    def test_basic_creation_with_all_fields(self) -> None:
        role = RoleInfo(
            global_role="superadmin",
            domain_role="admin",
            group_role="member",
        )
        assert role.global_role == "superadmin"
        assert role.domain_role == "admin"
        assert role.group_role == "member"

    def test_creation_without_group_role(self) -> None:
        role = RoleInfo(
            global_role="user",
            domain_role="user",
        )
        assert role.global_role == "user"
        assert role.domain_role == "user"
        assert role.group_role is None

    def test_creation_with_explicit_none_group_role(self) -> None:
        role = RoleInfo(
            global_role="user",
            domain_role="admin",
            group_role=None,
        )
        assert role.group_role is None

    def test_creation_from_dict(self) -> None:
        role = RoleInfo.model_validate({
            "global_role": "superadmin",
            "domain_role": "admin",
            "group_role": "owner",
        })
        assert role.global_role == "superadmin"
        assert role.group_role == "owner"

    def test_creation_from_dict_without_group_role(self) -> None:
        role = RoleInfo.model_validate({
            "global_role": "user",
            "domain_role": "user",
        })
        assert role.group_role is None


class TestRoleInfoSerialization:
    """Tests for RoleInfo serialization."""

    def test_model_dump_with_group_role(self) -> None:
        role = RoleInfo(
            global_role="superadmin",
            domain_role="admin",
            group_role="member",
        )
        data = role.model_dump()
        assert data["global_role"] == "superadmin"
        assert data["domain_role"] == "admin"
        assert data["group_role"] == "member"

    def test_model_dump_without_group_role(self) -> None:
        role = RoleInfo(
            global_role="user",
            domain_role="user",
        )
        data = role.model_dump()
        assert data["group_role"] is None

    def test_model_dump_json(self) -> None:
        role = RoleInfo(
            global_role="superadmin",
            domain_role="admin",
            group_role=None,
        )
        json_str = role.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["global_role"] == "superadmin"
        assert parsed["group_role"] is None

    def test_serialization_round_trip_with_group_role(self) -> None:
        role = RoleInfo(
            global_role="superadmin",
            domain_role="admin",
            group_role="owner",
        )
        json_str = role.model_dump_json()
        restored = RoleInfo.model_validate_json(json_str)
        assert restored.global_role == role.global_role
        assert restored.domain_role == role.domain_role
        assert restored.group_role == role.group_role

    def test_serialization_round_trip_without_group_role(self) -> None:
        role = RoleInfo(
            global_role="user",
            domain_role="user",
        )
        json_str = role.model_dump_json()
        restored = RoleInfo.model_validate_json(json_str)
        assert restored.global_role == role.global_role
        assert restored.group_role is None


class TestSSHKeypairInfoCreation:
    """Tests for SSHKeypairInfo Pydantic model creation."""

    def test_basic_creation(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa AAAAB3NzaC1yc2E...",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\n...",
        )
        assert keypair.ssh_public_key == "ssh-rsa AAAAB3NzaC1yc2E..."
        assert keypair.ssh_private_key == "-----BEGIN RSA PRIVATE KEY-----\n..."

    def test_creation_from_dict(self) -> None:
        keypair = SSHKeypairInfo.model_validate({
            "ssh_public_key": "ssh-rsa AAAA...",
            "ssh_private_key": "-----BEGIN RSA PRIVATE KEY-----",
        })
        assert keypair.ssh_public_key == "ssh-rsa AAAA..."


class TestSSHKeypairInfoSerialization:
    """Tests for SSHKeypairInfo serialization."""

    def test_model_dump(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa AAAA...",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----",
        )
        data = keypair.model_dump()
        assert data["ssh_public_key"] == "ssh-rsa AAAA..."
        assert data["ssh_private_key"] == "-----BEGIN RSA PRIVATE KEY-----"

    def test_model_dump_json(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa AAAA...",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----",
        )
        json_str = keypair.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["ssh_public_key"] == "ssh-rsa AAAA..."

    def test_serialization_round_trip(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa AAAAB3...",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\nMIIEow...",
        )
        json_str = keypair.model_dump_json()
        restored = SSHKeypairInfo.model_validate_json(json_str)
        assert restored.ssh_public_key == keypair.ssh_public_key
        assert restored.ssh_private_key == keypair.ssh_private_key


class TestPasswordChangeInfoCreation:
    """Tests for PasswordChangeInfo Pydantic model creation."""

    def test_basic_creation(self) -> None:
        pci = PasswordChangeInfo(password_changed_at="2024-01-15T12:00:00Z")
        assert pci.password_changed_at == "2024-01-15T12:00:00Z"

    def test_creation_from_dict(self) -> None:
        pci = PasswordChangeInfo.model_validate({
            "password_changed_at": "2024-06-01T08:30:00+09:00",
        })
        assert pci.password_changed_at == "2024-06-01T08:30:00+09:00"


class TestPasswordChangeInfoSerialization:
    """Tests for PasswordChangeInfo serialization."""

    def test_model_dump(self) -> None:
        pci = PasswordChangeInfo(password_changed_at="2024-01-15T12:00:00Z")
        data = pci.model_dump()
        assert data["password_changed_at"] == "2024-01-15T12:00:00Z"

    def test_model_dump_json(self) -> None:
        pci = PasswordChangeInfo(password_changed_at="2024-01-15T12:00:00Z")
        json_str = pci.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["password_changed_at"] == "2024-01-15T12:00:00Z"

    def test_serialization_round_trip(self) -> None:
        pci = PasswordChangeInfo(password_changed_at="2024-03-17T09:00:00Z")
        json_str = pci.model_dump_json()
        restored = PasswordChangeInfo.model_validate_json(json_str)
        assert restored.password_changed_at == pci.password_changed_at
