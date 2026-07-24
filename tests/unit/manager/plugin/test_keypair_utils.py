from __future__ import annotations

import pytest

from ai.backend.manager.plugin.keypair.exception import ExpiredSToken, InvalidSToken
from ai.backend.manager.plugin.keypair.utils import (
    STokenData,
    decode_jwt_token,
    deserialize_stoken,
    encode_jwt_token,
    serialize_stoken,
)

_SECRET = "test-token-secret"
_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"


class TestSToken:
    def test_roundtrip_preserves_access_key(self) -> None:
        token = serialize_stoken(STokenData(access_key=_ACCESS_KEY), _SECRET)
        restored = deserialize_stoken(token, _SECRET)
        assert restored.access_key == _ACCESS_KEY

    def test_payload_omits_secret_key(self) -> None:
        token = serialize_stoken(STokenData(access_key=_ACCESS_KEY), _SECRET)
        payload = decode_jwt_token(token, _SECRET)
        assert payload["access_key"] == _ACCESS_KEY
        assert "secret_key" not in payload

    def test_payload_has_expiry_claims(self) -> None:
        token = serialize_stoken(STokenData(access_key=_ACCESS_KEY), _SECRET)
        payload = decode_jwt_token(token, _SECRET)
        assert "iat" in payload
        assert "exp" in payload
        assert payload["exp"] > payload["iat"]

    @pytest.mark.parametrize("missing_claim", ["iat", "exp"])
    def test_missing_temporal_claim_raises(self, missing_claim: str) -> None:
        token = serialize_stoken(STokenData(access_key=_ACCESS_KEY), _SECRET)
        payload = dict(decode_jwt_token(token, _SECRET))
        payload.pop(missing_claim)

        with pytest.raises(InvalidSToken):
            deserialize_stoken(encode_jwt_token(payload, _SECRET), _SECRET)

    def test_expired_token_raises(self) -> None:
        # Negative TTL beyond the leeway window so the token is already expired on decode.
        token = serialize_stoken(STokenData(access_key=_ACCESS_KEY), _SECRET, ttl_seconds=-20)
        with pytest.raises(ExpiredSToken):
            deserialize_stoken(token, _SECRET)

    def test_wrong_secret_raises(self) -> None:
        token = serialize_stoken(STokenData(access_key=_ACCESS_KEY), _SECRET)
        with pytest.raises(InvalidSToken):
            deserialize_stoken(token, "wrong-secret")
