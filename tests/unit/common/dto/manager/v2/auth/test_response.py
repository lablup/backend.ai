"""Tests for ai.backend.common.dto.manager.v2.auth.response module."""

from __future__ import annotations

import json

from ai.backend.common.dto.manager.v2.auth.response import (
    AuthorizePayload,
    GetRolePayload,
    GetSSHKeypairPayload,
    SignoutPayload,
    SignupPayload,
    SSHKeypairPayload,
    UpdateFullNamePayload,
    UpdatePasswordNoAuthPayload,
    UpdatePasswordPayload,
    VerifyAuthPayload,
)
from ai.backend.common.dto.manager.v2.auth.types import (
    AuthCredentialInfo,
    PasswordChangeInfo,
    RoleInfo,
    SSHKeypairInfo,
)


class TestAuthorizePayload:
    """Tests for AuthorizePayload model with nested AuthCredentialInfo."""

    def test_creation_with_nested_credential_info(self) -> None:
        credential = AuthCredentialInfo(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            role="user",
            status="active",
        )
        payload = AuthorizePayload(data=credential)
        assert payload.data.access_key == "AKIAIOSFODNN7EXAMPLE"
        assert payload.data.secret_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert payload.data.role == "user"
        assert payload.data.status == "active"

    def test_nested_fields_accessible_via_payload(self) -> None:
        credential = AuthCredentialInfo(
            access_key="AKID",
            secret_key="SECRET",
            role="superadmin",
            status="active",
        )
        payload = AuthorizePayload(data=credential)
        assert payload.data.role == "superadmin"

    def test_json_round_trip(self) -> None:
        credential = AuthCredentialInfo(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            role="user",
            status="active",
        )
        payload = AuthorizePayload(data=credential)
        json_str = payload.model_dump_json()
        restored = AuthorizePayload.model_validate_json(json_str)
        assert restored.data.access_key == payload.data.access_key
        assert restored.data.secret_key == payload.data.secret_key
        assert restored.data.role == payload.data.role
        assert restored.data.status == payload.data.status

    def test_nested_data_structure_in_json(self) -> None:
        credential = AuthCredentialInfo(
            access_key="AK",
            secret_key="SK",
            role="user",
            status="active",
        )
        payload = AuthorizePayload(data=credential)
        data = json.loads(payload.model_dump_json())
        assert "data" in data
        assert isinstance(data["data"], dict)
        assert data["data"]["access_key"] == "AK"
        assert data["data"]["role"] == "user"


class TestSignupPayload:
    """Tests for SignupPayload model creation and field access."""

    def test_creation_with_keypair(self) -> None:
        payload = SignupPayload(
            access_key="NEWAK123",
            secret_key="NEWSK456",
        )
        assert payload.access_key == "NEWAK123"
        assert payload.secret_key == "NEWSK456"

    def test_access_key_and_secret_key_are_distinct(self) -> None:
        payload = SignupPayload(access_key="AK", secret_key="SK")
        assert payload.access_key != payload.secret_key

    def test_round_trip(self) -> None:
        payload = SignupPayload(access_key="NEWAK123", secret_key="NEWSK456")
        json_str = payload.model_dump_json()
        restored = SignupPayload.model_validate_json(json_str)
        assert restored.access_key == payload.access_key
        assert restored.secret_key == payload.secret_key


class TestSignoutPayload:
    """Tests for SignoutPayload (empty payload)."""

    def test_creation_with_no_fields(self) -> None:
        payload = SignoutPayload()
        assert payload is not None

    def test_serializes_to_empty_dict(self) -> None:
        payload = SignoutPayload()
        data = json.loads(payload.model_dump_json())
        assert data == {}

    def test_round_trip_empty(self) -> None:
        payload = SignoutPayload()
        json_str = payload.model_dump_json()
        restored = SignoutPayload.model_validate_json(json_str)
        assert isinstance(restored, SignoutPayload)


class TestVerifyAuthPayload:
    """Tests for VerifyAuthPayload with echo field preserved in round-trip."""

    def test_creation_with_required_fields(self) -> None:
        payload = VerifyAuthPayload(authorized="yes", echo="test_echo_value")
        assert payload.authorized == "yes"
        assert payload.echo == "test_echo_value"

    def test_echo_field_preserved_in_round_trip(self) -> None:
        original_echo = "my_unique_echo_string_12345"
        payload = VerifyAuthPayload(authorized="yes", echo=original_echo)
        json_str = payload.model_dump_json()
        restored = VerifyAuthPayload.model_validate_json(json_str)
        assert restored.echo == original_echo
        assert restored.authorized == "yes"

    def test_authorized_and_echo_in_json(self) -> None:
        payload = VerifyAuthPayload(authorized="yes", echo="ping")
        data = json.loads(payload.model_dump_json())
        assert data["authorized"] == "yes"
        assert data["echo"] == "ping"


class TestGetRolePayload:
    """Tests for GetRolePayload with nested RoleInfo."""

    def test_creation_with_role_info(self) -> None:
        role = RoleInfo(global_role="superadmin", domain_role="admin")
        payload = GetRolePayload(role=role)
        assert payload.role.global_role == "superadmin"
        assert payload.role.domain_role == "admin"
        assert payload.role.group_role is None

    def test_role_info_with_optional_group_role(self) -> None:
        role = RoleInfo(
            global_role="user",
            domain_role="user",
            group_role="member",
        )
        payload = GetRolePayload(role=role)
        assert payload.role.group_role == "member"

    def test_role_info_group_role_defaults_to_none(self) -> None:
        role = RoleInfo(global_role="user", domain_role="user")
        payload = GetRolePayload(role=role)
        assert payload.role.group_role is None

    def test_round_trip_preserves_all_role_fields(self) -> None:
        role = RoleInfo(
            global_role="superadmin",
            domain_role="admin",
            group_role="owner",
        )
        payload = GetRolePayload(role=role)
        json_str = payload.model_dump_json()
        restored = GetRolePayload.model_validate_json(json_str)
        assert restored.role.global_role == "superadmin"
        assert restored.role.domain_role == "admin"
        assert restored.role.group_role == "owner"

    def test_round_trip_without_group_role(self) -> None:
        role = RoleInfo(global_role="user", domain_role="user")
        payload = GetRolePayload(role=role)
        json_str = payload.model_dump_json()
        restored = GetRolePayload.model_validate_json(json_str)
        assert restored.role.group_role is None

    def test_nested_role_structure_in_json(self) -> None:
        role = RoleInfo(global_role="user", domain_role="admin")
        payload = GetRolePayload(role=role)
        data = json.loads(payload.model_dump_json())
        assert "role" in data
        assert isinstance(data["role"], dict)
        assert data["role"]["global_role"] == "user"
        assert data["role"]["domain_role"] == "admin"


class TestUpdateFullNamePayload:
    """Tests for UpdateFullNamePayload (empty payload)."""

    def test_creation_with_no_fields(self) -> None:
        payload = UpdateFullNamePayload()
        assert payload is not None

    def test_serializes_to_empty_dict(self) -> None:
        payload = UpdateFullNamePayload()
        data = json.loads(payload.model_dump_json())
        assert data == {}

    def test_round_trip_empty(self) -> None:
        payload = UpdateFullNamePayload()
        json_str = payload.model_dump_json()
        restored = UpdateFullNamePayload.model_validate_json(json_str)
        assert isinstance(restored, UpdateFullNamePayload)


class TestUpdatePasswordPayload:
    """Tests for UpdatePasswordPayload with optional error_msg."""

    def test_creation_with_no_error_on_success(self) -> None:
        payload = UpdatePasswordPayload()
        assert payload.error_msg is None

    def test_creation_with_explicit_none(self) -> None:
        payload = UpdatePasswordPayload(error_msg=None)
        assert payload.error_msg is None

    def test_creation_with_error_message(self) -> None:
        payload = UpdatePasswordPayload(error_msg="New password does not match confirmation")
        assert payload.error_msg == "New password does not match confirmation"

    def test_round_trip_with_none_error(self) -> None:
        payload = UpdatePasswordPayload()
        json_str = payload.model_dump_json()
        restored = UpdatePasswordPayload.model_validate_json(json_str)
        assert restored.error_msg is None

    def test_round_trip_with_error_message(self) -> None:
        payload = UpdatePasswordPayload(error_msg="Mismatch")
        json_str = payload.model_dump_json()
        restored = UpdatePasswordPayload.model_validate_json(json_str)
        assert restored.error_msg == "Mismatch"


class TestUpdatePasswordNoAuthPayload:
    """Tests for UpdatePasswordNoAuthPayload with nested PasswordChangeInfo."""

    def test_creation_with_password_change_info(self) -> None:
        change_info = PasswordChangeInfo(password_changed_at="2026-03-17T10:00:00Z")
        payload = UpdatePasswordNoAuthPayload(password_change=change_info)
        assert payload.password_change.password_changed_at == "2026-03-17T10:00:00Z"

    def test_nested_timestamp_accessible(self) -> None:
        change_info = PasswordChangeInfo(password_changed_at="2026-01-01T00:00:00Z")
        payload = UpdatePasswordNoAuthPayload(password_change=change_info)
        assert "2026" in payload.password_change.password_changed_at

    def test_round_trip(self) -> None:
        change_info = PasswordChangeInfo(password_changed_at="2026-03-17T10:00:00Z")
        payload = UpdatePasswordNoAuthPayload(password_change=change_info)
        json_str = payload.model_dump_json()
        restored = UpdatePasswordNoAuthPayload.model_validate_json(json_str)
        assert restored.password_change.password_changed_at == "2026-03-17T10:00:00Z"

    def test_nested_structure_in_json(self) -> None:
        change_info = PasswordChangeInfo(password_changed_at="2026-03-17T10:00:00Z")
        payload = UpdatePasswordNoAuthPayload(password_change=change_info)
        data = json.loads(payload.model_dump_json())
        assert "password_change" in data
        assert isinstance(data["password_change"], dict)
        assert data["password_change"]["password_changed_at"] == "2026-03-17T10:00:00Z"


class TestGetSSHKeypairPayload:
    """Tests for GetSSHKeypairPayload with public key only."""

    def test_creation_with_public_key(self) -> None:
        payload = GetSSHKeypairPayload(ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAA...")
        assert payload.ssh_public_key == "ssh-rsa AAAAB3NzaC1yc2EAAA..."

    def test_round_trip(self) -> None:
        public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."
        payload = GetSSHKeypairPayload(ssh_public_key=public_key)
        json_str = payload.model_dump_json()
        restored = GetSSHKeypairPayload.model_validate_json(json_str)
        assert restored.ssh_public_key == public_key

    def test_public_key_in_json(self) -> None:
        payload = GetSSHKeypairPayload(ssh_public_key="ssh-rsa AAAA...")
        data = json.loads(payload.model_dump_json())
        assert "ssh_public_key" in data
        assert data["ssh_public_key"] == "ssh-rsa AAAA..."


class TestSSHKeypairPayload:
    """Tests for SSHKeypairPayload with nested SSHKeypairInfo."""

    def test_creation_with_keypair_info(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa AAAAB3NzaC1yc2E...",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\nMIIEow...",
        )
        payload = SSHKeypairPayload(keypair=keypair)
        assert payload.keypair.ssh_public_key == "ssh-rsa AAAAB3NzaC1yc2E..."
        assert payload.keypair.ssh_private_key == "-----BEGIN RSA PRIVATE KEY-----\nMIIEow..."

    def test_both_keys_accessible_via_payload(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa PUBKEY",
            ssh_private_key="-----BEGIN PRIVKEY-----",
        )
        payload = SSHKeypairPayload(keypair=keypair)
        assert payload.keypair.ssh_public_key == "ssh-rsa PUBKEY"
        assert payload.keypair.ssh_private_key == "-----BEGIN PRIVKEY-----"

    def test_round_trip(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA",
        )
        payload = SSHKeypairPayload(keypair=keypair)
        json_str = payload.model_dump_json()
        restored = SSHKeypairPayload.model_validate_json(json_str)
        assert restored.keypair.ssh_public_key == keypair.ssh_public_key
        assert restored.keypair.ssh_private_key == keypair.ssh_private_key

    def test_nested_keypair_structure_in_json(self) -> None:
        keypair = SSHKeypairInfo(
            ssh_public_key="ssh-rsa PUB",
            ssh_private_key="PRIV",
        )
        payload = SSHKeypairPayload(keypair=keypair)
        data = json.loads(payload.model_dump_json())
        assert "keypair" in data
        assert isinstance(data["keypair"], dict)
        assert data["keypair"]["ssh_public_key"] == "ssh-rsa PUB"
        assert data["keypair"]["ssh_private_key"] == "PRIV"
