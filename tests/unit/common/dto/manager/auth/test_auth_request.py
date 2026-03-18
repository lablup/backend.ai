from __future__ import annotations

from uuid import UUID, uuid4

from ai.backend.common.api_handlers import BaseRequestModel
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
from ai.backend.common.dto.manager.auth.types import AuthTokenType


def test_authorize_request_creation() -> None:
    req = AuthorizeRequest(
        type=AuthTokenType.KEYPAIR,
        domain="default",
        username="user@example.com",
        password="secret",
        stoken="abc123",
    )
    assert req.type == AuthTokenType.KEYPAIR
    assert req.domain == "default"
    assert req.username == "user@example.com"
    assert req.password == "secret"
    assert req.stoken == "abc123"


def test_authorize_request_stoken_alias() -> None:
    req = AuthorizeRequest.model_validate({
        "type": "keypair",
        "domain": "default",
        "username": "user@example.com",
        "password": "secret",
        "sToken": "from_alias",
    })
    assert req.stoken == "from_alias"


def test_authorize_request_stoken_default_none() -> None:
    req = AuthorizeRequest(
        type=AuthTokenType.JWT,
        domain="default",
        username="user@example.com",
        password="secret",
    )
    assert req.stoken is None


def test_get_role_request_default_group() -> None:
    req = GetRoleRequest()
    assert req.group is None


def test_get_role_request_with_group() -> None:
    gid = uuid4()
    req = GetRoleRequest(group=gid)
    assert req.group == gid
    assert isinstance(req.group, UUID)


def test_signup_request_required_fields() -> None:
    req = SignupRequest(
        domain="default",
        email="new@example.com",
        password="strongpw",
    )
    assert req.domain == "default"
    assert req.email == "new@example.com"
    assert req.password == "strongpw"


def test_signup_request_optional_fields() -> None:
    req = SignupRequest(
        domain="default",
        email="new@example.com",
        password="strongpw",
    )
    assert req.username is None
    assert req.full_name is None
    assert req.description is None


def test_signup_request_with_optional_fields() -> None:
    req = SignupRequest(
        domain="default",
        email="new@example.com",
        password="strongpw",
        username="newuser",
        full_name="New User",
        description="A test user",
    )
    assert req.username == "newuser"
    assert req.full_name == "New User"
    assert req.description == "A test user"


def test_signout_request_email_alias() -> None:
    req = SignoutRequest.model_validate({
        "username": "user@example.com",
        "password": "secret",
    })
    assert req.email == "user@example.com"


def test_signout_request_with_email() -> None:
    req = SignoutRequest(
        email="user@example.com",
        password="secret",
    )
    assert req.email == "user@example.com"
    assert req.password == "secret"


def test_update_full_name_request() -> None:
    req = UpdateFullNameRequest(
        email="user@example.com",
        full_name="Updated Name",
    )
    assert req.email == "user@example.com"
    assert req.full_name == "Updated Name"


def test_update_password_request() -> None:
    req = UpdatePasswordRequest(
        old_password="oldpw",
        new_password="newpw",
        new_password2="newpw",
    )
    assert req.old_password == "oldpw"
    assert req.new_password == "newpw"
    assert req.new_password2 == "newpw"


def test_update_password_no_auth_request() -> None:
    req = UpdatePasswordNoAuthRequest(
        domain="default",
        username="user@example.com",
        current_password="expired",
        new_password="fresh",
    )
    assert req.domain == "default"
    assert req.username == "user@example.com"
    assert req.current_password == "expired"
    assert req.new_password == "fresh"


def test_upload_ssh_keypair_request() -> None:
    req = UploadSSHKeypairRequest(
        pubkey="ssh-rsa AAAA...",
        privkey="-----BEGIN RSA PRIVATE KEY-----...",
    )
    assert req.pubkey == "ssh-rsa AAAA..."
    assert req.privkey == "-----BEGIN RSA PRIVATE KEY-----..."


def test_verify_auth_request() -> None:
    req = VerifyAuthRequest(echo="hello")
    assert req.echo == "hello"


def test_request_models_have_field_descriptions() -> None:
    models: list[type[BaseRequestModel]] = [
        AuthorizeRequest,
        GetRoleRequest,
        SignupRequest,
        SignoutRequest,
        UpdateFullNameRequest,
        UpdatePasswordRequest,
        UpdatePasswordNoAuthRequest,
        UploadSSHKeypairRequest,
        VerifyAuthRequest,
    ]
    for model in models:
        schema = model.model_json_schema()
        assert "properties" in schema, f"{model.__name__} has no properties in schema"
        for field_name, field_info in schema["properties"].items():
            assert "description" in field_info, (
                f"{model.__name__}.{field_name} is missing a Field description"
            )


def test_request_serialization_round_trip() -> None:
    req = AuthorizeRequest(
        type=AuthTokenType.KEYPAIR,
        domain="default",
        username="user@example.com",
        password="secret",
        stoken="token123",
    )
    json_data = req.model_dump_json()
    restored = AuthorizeRequest.model_validate_json(json_data)
    assert restored.type == req.type
    assert restored.domain == req.domain
    assert restored.username == req.username
    assert restored.password == req.password
    assert restored.stoken == req.stoken


def test_signup_request_serialization_round_trip() -> None:
    req = SignupRequest(
        domain="default",
        email="user@example.com",
        password="pw",
        username="testuser",
        full_name="Test User",
        description="desc",
    )
    json_data = req.model_dump_json()
    restored = SignupRequest.model_validate_json(json_data)
    assert restored.domain == req.domain
    assert restored.email == req.email
    assert restored.username == req.username
    assert restored.full_name == req.full_name
    assert restored.description == req.description
