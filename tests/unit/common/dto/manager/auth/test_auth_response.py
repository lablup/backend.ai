from __future__ import annotations

from ai.backend.common.api_handlers import BaseResponseModel
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
from ai.backend.common.dto.manager.auth.types import (
    AuthResponseType,
    AuthSuccessResponse,
    AuthTokenType,
)


def test_authorize_response() -> None:
    data = AuthSuccessResponse(
        response_type=AuthResponseType.SUCCESS,
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        role="user",
        status="active",
        type=AuthTokenType.KEYPAIR,
    )
    resp = AuthorizeResponse(data=data)
    assert resp.data.access_key == "AKIAIOSFODNN7EXAMPLE"
    assert resp.data.role == "user"
    assert resp.data.status == "active"


def test_get_role_response() -> None:
    resp = GetRoleResponse(
        global_role="superadmin",
        domain_role="admin",
        group_role="admin",
    )
    assert resp.global_role == "superadmin"
    assert resp.domain_role == "admin"
    assert resp.group_role == "admin"


def test_get_role_response_default_group_role() -> None:
    resp = GetRoleResponse(
        global_role="user",
        domain_role="user",
    )
    assert resp.group_role is None


def test_signup_response() -> None:
    resp = SignupResponse(
        access_key="AKTEST",
        secret_key="SKTEST",
    )
    assert resp.access_key == "AKTEST"
    assert resp.secret_key == "SKTEST"


def test_signout_response_empty() -> None:
    resp = SignoutResponse()
    assert isinstance(resp, SignoutResponse)


def test_update_full_name_response_empty() -> None:
    resp = UpdateFullNameResponse()
    assert isinstance(resp, UpdateFullNameResponse)


def test_update_password_response_success() -> None:
    resp = UpdatePasswordResponse()
    assert resp.error_msg is None


def test_update_password_response_failure() -> None:
    resp = UpdatePasswordResponse(error_msg="New passwords do not match")
    assert resp.error_msg == "New passwords do not match"


def test_update_password_no_auth_response() -> None:
    resp = UpdatePasswordNoAuthResponse(
        password_changed_at="2025-01-15T10:30:00+00:00",
    )
    assert resp.password_changed_at == "2025-01-15T10:30:00+00:00"


def test_get_ssh_keypair_response() -> None:
    resp = GetSSHKeypairResponse(
        ssh_public_key="ssh-rsa AAAA...",
    )
    assert resp.ssh_public_key == "ssh-rsa AAAA..."


def test_ssh_keypair_response() -> None:
    resp = SSHKeypairResponse(
        ssh_public_key="ssh-rsa AAAA...",
        ssh_private_key="-----BEGIN RSA PRIVATE KEY-----...",
    )
    assert resp.ssh_public_key == "ssh-rsa AAAA..."
    assert resp.ssh_private_key == "-----BEGIN RSA PRIVATE KEY-----..."


def test_verify_auth_response() -> None:
    resp = VerifyAuthResponse(
        authorized="yes",
        echo="hello",
    )
    assert resp.authorized == "yes"
    assert resp.echo == "hello"


def test_response_models_have_field_descriptions() -> None:
    models_with_fields: list[type[BaseResponseModel]] = [
        AuthorizeResponse,
        GetRoleResponse,
        SignupResponse,
        UpdatePasswordResponse,
        UpdatePasswordNoAuthResponse,
        GetSSHKeypairResponse,
        SSHKeypairResponse,
        VerifyAuthResponse,
    ]
    for model in models_with_fields:
        schema = model.model_json_schema()
        assert "properties" in schema, f"{model.__name__} has no properties in schema"
        for field_name, field_info in schema["properties"].items():
            assert "description" in field_info, (
                f"{model.__name__}.{field_name} is missing a Field description"
            )


def test_response_serialization_round_trip() -> None:
    resp = GetRoleResponse(
        global_role="superadmin",
        domain_role="admin",
        group_role="user",
    )
    json_data = resp.model_dump_json()
    restored = GetRoleResponse.model_validate_json(json_data)
    assert restored.global_role == resp.global_role
    assert restored.domain_role == resp.domain_role
    assert restored.group_role == resp.group_role


def test_verify_auth_response_serialization_round_trip() -> None:
    resp = VerifyAuthResponse(authorized="yes", echo="ping")
    json_data = resp.model_dump_json()
    restored = VerifyAuthResponse.model_validate_json(json_data)
    assert restored.authorized == resp.authorized
    assert restored.echo == resp.echo


def test_signup_response_serialization_round_trip() -> None:
    resp = SignupResponse(access_key="AK", secret_key="SK")
    json_data = resp.model_dump_json()
    restored = SignupResponse.model_validate_json(json_data)
    assert restored.access_key == resp.access_key
    assert restored.secret_key == resp.secret_key
