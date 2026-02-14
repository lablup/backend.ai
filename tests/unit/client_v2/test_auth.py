from datetime import UTC, datetime

from yarl import URL

from ai.backend.client.v2.auth import AuthStrategy, HMACAuth


class TestHMACAuth:
    def test_sign_returns_authorization_header(self) -> None:
        auth = HMACAuth(access_key="AKIAIOSFODNN7EXAMPLE", secret_key="test-secret-key")
        headers = auth.sign(
            method="GET",
            version="v9.20250722",
            endpoint=URL("https://api.example.com"),
            date=datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC),
            rel_url="/folders",
            content_type="application/json",
        )
        assert "Authorization" in headers
        assert "BackendAI" in headers["Authorization"]
        assert "HMAC-SHA256" in headers["Authorization"]
        assert "AKIAIOSFODNN7EXAMPLE" in headers["Authorization"]

    def test_sign_with_custom_hash_type(self) -> None:
        auth = HMACAuth(
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="test-secret-key",
            hash_type="sha512",
        )
        headers = auth.sign(
            method="POST",
            version="v9.20250722",
            endpoint=URL("https://api.example.com"),
            date=datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC),
            rel_url="/sessions",
            content_type="application/json",
        )
        assert "HMAC-SHA512" in headers["Authorization"]

    def test_is_auth_strategy_subclass(self) -> None:
        auth = HMACAuth(access_key="test", secret_key="test")
        assert isinstance(auth, AuthStrategy)
