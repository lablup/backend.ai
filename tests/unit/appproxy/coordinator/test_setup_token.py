from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import jwt
import pytest

from ai.backend.appproxy.coordinator.api.proxy import _SETUP_TOKEN_LIFETIME, _sign_setup_token

_TOKEN_ID = UUID("4eeb260b-6cc5-4362-baf3-ea978388becd")
_CIRCUIT_ID = UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372")
_JWT_SECRET = "a" * 32


class TestSignSetupToken:
    @pytest.fixture
    def signed_setup_token(self) -> str:
        return _sign_setup_token(_TOKEN_ID, _CIRCUIT_ID, "/lab", _JWT_SECRET)

    def test_token_names_the_circuit_and_the_redirect(self, signed_setup_token: str) -> None:
        claims = jwt.decode(signed_setup_token, _JWT_SECRET, algorithms=["HS256"])

        assert claims["id"] == str(_TOKEN_ID)
        assert claims["circuit"] == str(_CIRCUIT_ID)
        assert claims["redirect"] == "/lab"

    def test_token_expires_within_the_lifetime(self, signed_setup_token: str) -> None:
        now = datetime.now(UTC)

        claims = jwt.decode(signed_setup_token, _JWT_SECRET, algorithms=["HS256"])

        assert now.timestamp() < claims["exp"] <= (now + _SETUP_TOKEN_LIFETIME).timestamp()

    def test_tokens_with_the_same_input_are_distinct(self, signed_setup_token: str) -> None:
        another_token = _sign_setup_token(_TOKEN_ID, _CIRCUIT_ID, "/lab", _JWT_SECRET)

        claims = jwt.decode(signed_setup_token, _JWT_SECRET, algorithms=["HS256"])
        another_claims = jwt.decode(another_token, _JWT_SECRET, algorithms=["HS256"])
        assert claims["jti"] != another_claims["jti"]
