from __future__ import annotations

from ai.backend.common.dto.manager.auth.types import (
    AuthResponseType,
    AuthSuccessResponse,
    AuthTokenType,
    RequireTwoFactorAuthResponse,
    RequireTwoFactorRegistrationResponse,
    TwoFactorType,
    parse_auth_response,
)


def test_auth_token_type_values() -> None:
    assert AuthTokenType.KEYPAIR.value == "keypair"
    assert AuthTokenType.JWT.value == "jwt"
    assert AuthTokenType("keypair") == AuthTokenType.KEYPAIR
    assert AuthTokenType("jwt") == AuthTokenType.JWT


def test_auth_response_type_values() -> None:
    assert AuthResponseType.SUCCESS.value == "success"
    assert (
        AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION.value == "REQUIRE_TWO_FACTOR_REGISTRATION"
    )
    assert AuthResponseType.REQUIRE_TWO_FACTOR_AUTH.value == "REQUIRE_TWO_FACTOR_AUTH"


def test_two_factor_type_values() -> None:
    assert TwoFactorType.TOTP == "TOTP"
    assert TwoFactorType("TOTP") == TwoFactorType.TOTP


def test_auth_success_response_creation() -> None:
    resp = AuthSuccessResponse(
        response_type=AuthResponseType.SUCCESS,
        access_key="AKTEST",
        secret_key="SKTEST",
        role="user",
        status="active",
    )
    assert resp.access_key == "AKTEST"
    assert resp.secret_key == "SKTEST"
    assert resp.role == "user"
    assert resp.status == "active"
    assert resp.type == AuthTokenType.KEYPAIR


def test_auth_success_response_to_dict() -> None:
    resp = AuthSuccessResponse(
        response_type=AuthResponseType.SUCCESS,
        access_key="AK",
        secret_key="SK",
        role="admin",
        status="active",
        type=AuthTokenType.JWT,
    )
    d = resp.to_dict()
    assert d["access_key"] == "AK"
    assert d["secret_key"] == "SK"
    assert d["role"] == "admin"
    assert d["status"] == "active"
    assert d["type"] == "jwt"
    assert d["response_type"] == "success"


def test_require_two_factor_registration_response() -> None:
    resp = RequireTwoFactorRegistrationResponse(
        response_type=AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION,
        token="totp-setup-token-abc",
        type=TwoFactorType.TOTP,
    )
    assert resp.token == "totp-setup-token-abc"
    assert resp.type == TwoFactorType.TOTP
    assert resp.response_type == AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION


def test_require_two_factor_registration_response_to_dict() -> None:
    resp = RequireTwoFactorRegistrationResponse(
        response_type=AuthResponseType.REQUIRE_TWO_FACTOR_REGISTRATION,
        token="tok",
        type=TwoFactorType.TOTP,
    )
    d = resp.to_dict()
    assert d["token"] == "tok"
    assert d["type"] == "TOTP"


def test_require_two_factor_auth_response() -> None:
    resp = RequireTwoFactorAuthResponse(
        response_type=AuthResponseType.REQUIRE_TWO_FACTOR_AUTH,
        type=TwoFactorType.TOTP,
    )
    assert resp.type == TwoFactorType.TOTP
    assert resp.response_type == AuthResponseType.REQUIRE_TWO_FACTOR_AUTH


def test_require_two_factor_auth_response_to_dict() -> None:
    resp = RequireTwoFactorAuthResponse(
        response_type=AuthResponseType.REQUIRE_TWO_FACTOR_AUTH,
        type=TwoFactorType.TOTP,
    )
    d = resp.to_dict()
    assert d["type"] == "TOTP"
    assert d["response_type"] == "REQUIRE_TWO_FACTOR_AUTH"


def test_parse_auth_response_success() -> None:
    data = {
        "response_type": "success",
        "access_key": "AK",
        "secret_key": "SK",
        "role": "user",
        "status": "active",
    }
    result = parse_auth_response(data)
    assert isinstance(result, AuthSuccessResponse)
    assert result.access_key == "AK"


def test_parse_auth_response_two_factor_registration() -> None:
    data = {
        "response_type": "REQUIRE_TWO_FACTOR_REGISTRATION",
        "token": "setup-token",
        "type": "TOTP",
    }
    result = parse_auth_response(data)
    assert isinstance(result, RequireTwoFactorRegistrationResponse)
    assert result.token == "setup-token"


def test_parse_auth_response_two_factor_auth() -> None:
    data = {
        "response_type": "REQUIRE_TWO_FACTOR_AUTH",
        "type": "TOTP",
    }
    result = parse_auth_response(data)
    assert isinstance(result, RequireTwoFactorAuthResponse)
    assert result.type == TwoFactorType.TOTP


def test_parse_auth_response_explicit_success() -> None:
    data = {
        "response_type": "success",
        "access_key": "AK",
        "secret_key": "SK",
        "role": "user",
        "status": "active",
    }
    result = parse_auth_response(data)
    assert isinstance(result, AuthSuccessResponse)
    assert result.response_type == AuthResponseType.SUCCESS
