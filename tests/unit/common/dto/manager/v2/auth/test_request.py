"""Tests for ai.backend.common.dto.manager.v2.auth.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.auth.request import (
    AuthorizeInput,
    GetRoleInput,
    SignoutInput,
    SignupInput,
    UpdateFullNameInput,
    UpdatePasswordInput,
    UpdatePasswordNoAuthInput,
    UploadSSHKeypairInput,
    VerifyAuthInput,
)
from ai.backend.common.dto.manager.v2.auth.types import AuthTokenType


class TestAuthorizeInput:
    """Tests for AuthorizeInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = AuthorizeInput(
            type=AuthTokenType.KEYPAIR,
            domain="default",
            username="user@example.com",
            password="secret",
        )
        assert req.type == AuthTokenType.KEYPAIR
        assert req.domain == "default"
        assert req.username == "user@example.com"
        assert req.password == "secret"
        assert req.stoken is None

    def test_valid_creation_with_jwt_type(self) -> None:
        req = AuthorizeInput(
            type=AuthTokenType.JWT,
            domain="default",
            username="user@example.com",
            password="secret",
        )
        assert req.type == AuthTokenType.JWT

    def test_valid_creation_with_stoken(self) -> None:
        req = AuthorizeInput(
            type=AuthTokenType.KEYPAIR,
            domain="default",
            username="user@example.com",
            password="secret",
            stoken="mytoken123",
        )
        assert req.stoken == "mytoken123"

    def test_stoken_alias_choices_stoken(self) -> None:
        req = AuthorizeInput.model_validate({
            "type": "keypair",
            "domain": "default",
            "username": "user@example.com",
            "password": "secret",
            "stoken": "tok1",
        })
        assert req.stoken == "tok1"

    def test_stoken_alias_choices_sToken(self) -> None:
        req = AuthorizeInput.model_validate({
            "type": "keypair",
            "domain": "default",
            "username": "user@example.com",
            "password": "secret",
            "sToken": "tok2",
        })
        assert req.stoken == "tok2"

    def test_otp_field(self) -> None:
        req = AuthorizeInput.model_validate({
            "type": "keypair",
            "domain": "default",
            "username": "user@example.com",
            "password": "secret",
            "otp": "123456",
        })
        assert req.otp == "123456"
        assert req.stoken is None

    def test_stoken_defaults_to_none(self) -> None:
        req = AuthorizeInput(
            type=AuthTokenType.KEYPAIR,
            domain="default",
            username="user@example.com",
            password="secret",
        )
        assert req.stoken is None

    def test_missing_type_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AuthorizeInput.model_validate({
                "domain": "default",
                "username": "user@example.com",
                "password": "secret",
            })

    def test_missing_domain_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AuthorizeInput.model_validate({
                "type": "keypair",
                "username": "user@example.com",
                "password": "secret",
            })

    def test_empty_domain_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AuthorizeInput(
                type=AuthTokenType.KEYPAIR,
                domain="",
                username="user@example.com",
                password="secret",
            )

    def test_empty_username_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AuthorizeInput(
                type=AuthTokenType.KEYPAIR,
                domain="default",
                username="",
                password="secret",
            )

    def test_empty_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AuthorizeInput(
                type=AuthTokenType.KEYPAIR,
                domain="default",
                username="user@example.com",
                password="",
            )

    def test_invalid_type_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            AuthorizeInput.model_validate({
                "type": "invalid_type",
                "domain": "default",
                "username": "user@example.com",
                "password": "secret",
            })


class TestAuthorizeInputRoundTrip:
    """Tests for AuthorizeInput serialization round-trip."""

    def test_round_trip_with_all_fields(self) -> None:
        req = AuthorizeInput(
            type=AuthTokenType.JWT,
            domain="default",
            username="user@example.com",
            password="secret",
            stoken="mytoken",
        )
        json_data = req.model_dump_json()
        restored = AuthorizeInput.model_validate_json(json_data)
        assert restored.type == req.type
        assert restored.domain == req.domain
        assert restored.username == req.username
        assert restored.password == req.password
        assert restored.stoken == req.stoken

    def test_round_trip_without_stoken(self) -> None:
        req = AuthorizeInput(
            type=AuthTokenType.KEYPAIR,
            domain="default",
            username="user@example.com",
            password="secret",
        )
        json_data = req.model_dump_json()
        restored = AuthorizeInput.model_validate_json(json_data)
        assert restored.type == req.type
        assert restored.stoken is None


class TestSignupInput:
    """Tests for SignupInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = SignupInput(
            domain="default",
            email="user@example.com",
            password="secret",
        )
        assert req.domain == "default"
        assert req.email == "user@example.com"
        assert req.password == "secret"
        assert req.username is None
        assert req.full_name is None
        assert req.description is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = SignupInput(
            domain="default",
            email="user@example.com",
            password="secret",
            username="myuser",
            full_name="My User",
            description="A test user",
        )
        assert req.username == "myuser"
        assert req.full_name == "My User"
        assert req.description == "A test user"

    def test_email_whitespace_is_stripped(self) -> None:
        req = SignupInput(
            domain="default",
            email="  user@example.com  ",
            password="secret",
        )
        assert req.email == "user@example.com"

    def test_username_whitespace_is_stripped(self) -> None:
        req = SignupInput(
            domain="default",
            email="user@example.com",
            password="secret",
            username="  myuser  ",
        )
        assert req.username == "myuser"

    def test_username_whitespace_only_becomes_none(self) -> None:
        req = SignupInput(
            domain="default",
            email="user@example.com",
            password="secret",
            username="   ",
        )
        assert req.username is None

    def test_full_name_whitespace_is_stripped(self) -> None:
        req = SignupInput(
            domain="default",
            email="user@example.com",
            password="secret",
            full_name="  Full Name  ",
        )
        assert req.full_name == "Full Name"

    def test_full_name_whitespace_only_becomes_none(self) -> None:
        req = SignupInput(
            domain="default",
            email="user@example.com",
            password="secret",
            full_name="   ",
        )
        assert req.full_name is None

    def test_empty_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignupInput(domain="default", email="", password="secret")

    def test_whitespace_only_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignupInput(domain="default", email="   ", password="secret")

    def test_missing_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignupInput.model_validate({"domain": "default", "password": "secret"})

    def test_missing_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignupInput.model_validate({
                "domain": "default",
                "email": "user@example.com",
            })

    def test_empty_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignupInput(domain="default", email="user@example.com", password="")


class TestSignupInputRoundTrip:
    """Tests for SignupInput serialization round-trip."""

    def test_round_trip_with_all_fields(self) -> None:
        req = SignupInput(
            domain="default",
            email="user@example.com",
            password="secret",
            username="myuser",
            full_name="My User",
            description="A description",
        )
        json_data = req.model_dump_json()
        restored = SignupInput.model_validate_json(json_data)
        assert restored.domain == req.domain
        assert restored.email == req.email
        assert restored.username == req.username
        assert restored.full_name == req.full_name
        assert restored.description == req.description

    def test_round_trip_with_minimal_fields(self) -> None:
        req = SignupInput(domain="default", email="user@example.com", password="secret")
        json_data = req.model_dump_json()
        restored = SignupInput.model_validate_json(json_data)
        assert restored.email == req.email
        assert restored.username is None
        assert restored.full_name is None
        assert restored.description is None


class TestSignoutInput:
    """Tests for SignoutInput model creation and validation."""

    def test_valid_creation_with_email_field(self) -> None:
        req = SignoutInput(email="user@example.com", password="secret")
        assert req.email == "user@example.com"
        assert req.password == "secret"

    def test_alias_choices_email(self) -> None:
        req = SignoutInput.model_validate({
            "email": "user@example.com",
            "password": "secret",
        })
        assert req.email == "user@example.com"

    def test_alias_choices_username(self) -> None:
        req = SignoutInput.model_validate({
            "username": "user@example.com",
            "password": "secret",
        })
        assert req.email == "user@example.com"

    def test_email_whitespace_is_stripped(self) -> None:
        req = SignoutInput(email="  user@example.com  ", password="secret")
        assert req.email == "user@example.com"

    def test_empty_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignoutInput(email="", password="secret")

    def test_whitespace_only_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignoutInput(email="   ", password="secret")

    def test_empty_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignoutInput(email="user@example.com", password="")

    def test_missing_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SignoutInput.model_validate({"password": "secret"})


class TestSignoutInputRoundTrip:
    """Tests for SignoutInput serialization round-trip."""

    def test_round_trip(self) -> None:
        req = SignoutInput(email="user@example.com", password="secret")
        json_data = req.model_dump_json()
        restored = SignoutInput.model_validate_json(json_data)
        assert restored.email == req.email
        assert restored.password == req.password


class TestVerifyAuthInput:
    """Tests for VerifyAuthInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = VerifyAuthInput(echo="hello")
        assert req.echo == "hello"

    def test_valid_creation_from_dict(self) -> None:
        req = VerifyAuthInput.model_validate({"echo": "test_echo"})
        assert req.echo == "test_echo"

    def test_empty_echo_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            VerifyAuthInput(echo="")

    def test_missing_echo_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            VerifyAuthInput.model_validate({})

    def test_echo_at_max_length_is_valid(self) -> None:
        req = VerifyAuthInput(echo="a" * 256)
        assert len(req.echo) == 256

    def test_echo_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            VerifyAuthInput(echo="a" * 257)


class TestVerifyAuthInputRoundTrip:
    """Tests for VerifyAuthInput serialization round-trip."""

    def test_round_trip(self) -> None:
        req = VerifyAuthInput(echo="my_echo_value")
        json_data = req.model_dump_json()
        restored = VerifyAuthInput.model_validate_json(json_data)
        assert restored.echo == req.echo


class TestGetRoleInput:
    """Tests for GetRoleInput model creation and validation."""

    def test_valid_creation_without_group(self) -> None:
        req = GetRoleInput()
        assert req.group is None

    def test_valid_creation_with_none_group(self) -> None:
        req = GetRoleInput(group=None)
        assert req.group is None

    def test_valid_creation_with_uuid_group(self) -> None:
        group_id = uuid.uuid4()
        req = GetRoleInput(group=group_id)
        assert req.group == group_id

    def test_valid_creation_from_uuid_string(self) -> None:
        group_id = uuid.uuid4()
        req = GetRoleInput.model_validate({"group": str(group_id)})
        assert req.group == group_id

    def test_invalid_uuid_string_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetRoleInput.model_validate({"group": "not-a-uuid"})

    def test_group_is_uuid_instance(self) -> None:
        group_id = uuid.uuid4()
        req = GetRoleInput(group=group_id)
        assert isinstance(req.group, uuid.UUID)


class TestGetRoleInputRoundTrip:
    """Tests for GetRoleInput serialization round-trip."""

    def test_round_trip_with_group(self) -> None:
        group_id = uuid.uuid4()
        req = GetRoleInput(group=group_id)
        json_data = req.model_dump_json()
        restored = GetRoleInput.model_validate_json(json_data)
        assert restored.group == req.group

    def test_round_trip_without_group(self) -> None:
        req = GetRoleInput()
        json_data = req.model_dump_json()
        restored = GetRoleInput.model_validate_json(json_data)
        assert restored.group is None


class TestUpdateFullNameInput:
    """Tests for UpdateFullNameInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = UpdateFullNameInput(email="user@example.com", full_name="John Doe")
        assert req.email == "user@example.com"
        assert req.full_name == "John Doe"

    def test_email_whitespace_is_stripped(self) -> None:
        req = UpdateFullNameInput(email="  user@example.com  ", full_name="John Doe")
        assert req.email == "user@example.com"

    def test_full_name_whitespace_is_stripped(self) -> None:
        req = UpdateFullNameInput(email="user@example.com", full_name="  John Doe  ")
        assert req.full_name == "John Doe"

    def test_empty_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateFullNameInput(email="", full_name="John Doe")

    def test_whitespace_only_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateFullNameInput(email="   ", full_name="John Doe")

    def test_empty_full_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateFullNameInput(email="user@example.com", full_name="")

    def test_whitespace_only_full_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateFullNameInput(email="user@example.com", full_name="   ")

    def test_missing_email_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateFullNameInput.model_validate({"full_name": "John Doe"})

    def test_missing_full_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateFullNameInput.model_validate({"email": "user@example.com"})


class TestUpdateFullNameInputRoundTrip:
    """Tests for UpdateFullNameInput serialization round-trip."""

    def test_round_trip(self) -> None:
        req = UpdateFullNameInput(email="user@example.com", full_name="John Doe")
        json_data = req.model_dump_json()
        restored = UpdateFullNameInput.model_validate_json(json_data)
        assert restored.email == req.email
        assert restored.full_name == req.full_name


class TestUpdatePasswordInput:
    """Tests for UpdatePasswordInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = UpdatePasswordInput(
            old_password="oldpass",
            new_password="newpass",
            new_password_confirm="newpass",
        )
        assert req.old_password == "oldpass"
        assert req.new_password == "newpass"
        assert req.new_password_confirm == "newpass"

    def test_empty_old_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordInput(
                old_password="",
                new_password="newpass",
                new_password_confirm="newpass",
            )

    def test_empty_new_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordInput(
                old_password="oldpass",
                new_password="",
                new_password_confirm="newpass",
            )

    def test_empty_new_password_confirm_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordInput(
                old_password="oldpass",
                new_password="newpass",
                new_password_confirm="",
            )

    def test_missing_old_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordInput.model_validate({
                "new_password": "newpass",
                "new_password_confirm": "newpass",
            })

    def test_missing_new_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordInput.model_validate({
                "old_password": "oldpass",
                "new_password_confirm": "newpass",
            })

    def test_missing_new_password_confirm_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordInput.model_validate({
                "old_password": "oldpass",
                "new_password": "newpass",
            })


class TestUpdatePasswordInputRoundTrip:
    """Tests for UpdatePasswordInput serialization round-trip."""

    def test_round_trip(self) -> None:
        req = UpdatePasswordInput(
            old_password="oldpass",
            new_password="newpass",
            new_password_confirm="newpass",
        )
        json_data = req.model_dump_json()
        restored = UpdatePasswordInput.model_validate_json(json_data)
        assert restored.old_password == req.old_password
        assert restored.new_password == req.new_password
        assert restored.new_password_confirm == req.new_password_confirm


class TestUpdatePasswordNoAuthInput:
    """Tests for UpdatePasswordNoAuthInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = UpdatePasswordNoAuthInput(
            domain="default",
            username="user@example.com",
            current_password="oldpass",
            new_password="newpass",
        )
        assert req.domain == "default"
        assert req.username == "user@example.com"
        assert req.current_password == "oldpass"
        assert req.new_password == "newpass"

    def test_empty_domain_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordNoAuthInput(
                domain="",
                username="user@example.com",
                current_password="oldpass",
                new_password="newpass",
            )

    def test_empty_username_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordNoAuthInput(
                domain="default",
                username="",
                current_password="oldpass",
                new_password="newpass",
            )

    def test_empty_current_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordNoAuthInput(
                domain="default",
                username="user@example.com",
                current_password="",
                new_password="newpass",
            )

    def test_empty_new_password_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordNoAuthInput(
                domain="default",
                username="user@example.com",
                current_password="oldpass",
                new_password="",
            )

    def test_missing_any_field_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdatePasswordNoAuthInput.model_validate({
                "domain": "default",
                "username": "user@example.com",
                "current_password": "oldpass",
            })


class TestUpdatePasswordNoAuthInputRoundTrip:
    """Tests for UpdatePasswordNoAuthInput serialization round-trip."""

    def test_round_trip(self) -> None:
        req = UpdatePasswordNoAuthInput(
            domain="default",
            username="user@example.com",
            current_password="oldpass",
            new_password="newpass",
        )
        json_data = req.model_dump_json()
        restored = UpdatePasswordNoAuthInput.model_validate_json(json_data)
        assert restored.domain == req.domain
        assert restored.username == req.username
        assert restored.current_password == req.current_password
        assert restored.new_password == req.new_password


class TestUploadSSHKeypairInput:
    """Tests for UploadSSHKeypairInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = UploadSSHKeypairInput(
            pubkey="ssh-rsa AAAAB3NzaC1yc2E...",
            privkey="-----BEGIN RSA PRIVATE KEY-----\nMIIEow...",
        )
        assert req.pubkey == "ssh-rsa AAAAB3NzaC1yc2E..."
        assert req.privkey == "-----BEGIN RSA PRIVATE KEY-----\nMIIEow..."

    def test_pubkey_whitespace_is_stripped(self) -> None:
        req = UploadSSHKeypairInput(
            pubkey="  ssh-rsa AAAA...  ",
            privkey="-----BEGIN RSA PRIVATE KEY-----",
        )
        assert req.pubkey == "ssh-rsa AAAA..."

    def test_privkey_whitespace_is_stripped(self) -> None:
        req = UploadSSHKeypairInput(
            pubkey="ssh-rsa AAAA...",
            privkey="  -----BEGIN RSA PRIVATE KEY-----  ",
        )
        assert req.privkey == "-----BEGIN RSA PRIVATE KEY-----"

    def test_empty_pubkey_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UploadSSHKeypairInput(
                pubkey="",
                privkey="-----BEGIN RSA PRIVATE KEY-----",
            )

    def test_whitespace_only_pubkey_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UploadSSHKeypairInput(
                pubkey="   ",
                privkey="-----BEGIN RSA PRIVATE KEY-----",
            )

    def test_empty_privkey_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UploadSSHKeypairInput(
                pubkey="ssh-rsa AAAA...",
                privkey="",
            )

    def test_whitespace_only_privkey_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UploadSSHKeypairInput(
                pubkey="ssh-rsa AAAA...",
                privkey="   ",
            )

    def test_missing_pubkey_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UploadSSHKeypairInput.model_validate({
                "privkey": "-----BEGIN RSA PRIVATE KEY-----",
            })

    def test_missing_privkey_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UploadSSHKeypairInput.model_validate({
                "pubkey": "ssh-rsa AAAA...",
            })


class TestUploadSSHKeypairInputRoundTrip:
    """Tests for UploadSSHKeypairInput serialization round-trip."""

    def test_round_trip(self) -> None:
        req = UploadSSHKeypairInput(
            pubkey="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ",
            privkey="-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA",
        )
        json_data = req.model_dump_json()
        restored = UploadSSHKeypairInput.model_validate_json(json_data)
        assert restored.pubkey == req.pubkey
        assert restored.privkey == req.privkey
