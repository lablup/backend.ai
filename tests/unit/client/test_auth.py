from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from dateutil.tz import tzutc

from ai.backend.client.auth import decrypt_payload, encrypt_payload, generate_signature
from ai.backend.client.func.auth import _put_secure_body
from ai.backend.client.request import Request
from ai.backend.client.session import api_session

if TYPE_CHECKING:
    from ai.backend.client.config import APIConfig


def _make_request_with_session(defconfig: APIConfig, method: str, path: str) -> Request:
    mock_session = MagicMock()
    mock_session.config = defconfig
    mock_session.api_version = (8, "20230615")
    token = api_session.set(mock_session)
    try:
        return Request(method, path)
    finally:
        api_session.reset(token)


def test_generate_signature(defconfig: APIConfig) -> None:
    kwargs: dict[str, Any] = dict(
        method="GET",
        version=defconfig.version,
        endpoint=defconfig.endpoint,
        date=datetime.now(tzutc()),
        rel_url="/path/to/api/",
        content_type="plain/text",
        access_key=defconfig.access_key,
        secret_key=defconfig.secret_key,
        hash_type="md5",
    )
    headers, signature = generate_signature(**kwargs)

    assert kwargs["hash_type"].upper() in headers["Authorization"]
    assert kwargs["access_key"] in headers["Authorization"]
    assert signature in headers["Authorization"]


def test_encrypt() -> None:
    endpoint = "https://example.com"
    orig = b"hello world"
    enc = encrypt_payload(endpoint, orig)
    print(repr(orig), repr(enc))
    dec = decrypt_payload(endpoint, enc)
    assert orig != enc
    assert orig == dec


def test_put_secure_body_encrypts_on_http(defconfig: APIConfig) -> None:
    """_put_secure_body encrypts the body when the endpoint is HTTP."""
    assert defconfig.endpoint.scheme == "http"
    rqst = _make_request_with_session(defconfig, "POST", "/test")
    body = {"username": "user", "password": "pass"}
    _put_secure_body(rqst, body)
    assert rqst.headers["X-BackendAI-Encoded"] == "true"
    assert rqst._content != json.dumps(body).encode()


def test_update_password_no_auth_does_not_encrypt(defconfig: APIConfig) -> None:
    """Regression: update_password_no_auth must send plain JSON, not encrypted body.

    This request goes directly to the manager, which has no decryption
    middleware for X-BackendAI-Encoded. Using _put_secure_body would cause
    the manager to fail with "Malformed body" on HTTP endpoints.
    """
    assert defconfig.endpoint.scheme == "http"
    rqst = _make_request_with_session(defconfig, "POST", "/auth/update-password-no-auth")
    body = {
        "domain": "default",
        "username": "user@example.com",
        "current_password": "old",
        "new_password": "new",
    }
    rqst.set_json(body)
    assert "X-BackendAI-Encoded" not in rqst.headers
    assert json.loads(rqst._content) == body
