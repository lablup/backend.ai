from __future__ import annotations

import pytest

from ai.backend.manager.plugin.totp.config import TOTPConfig
from ai.backend.manager.plugin.totp.utils import InvalidTokenError, TokenParser


class TestTokenParser:
    @pytest.fixture
    def token_parser(self) -> TokenParser:
        config = TOTPConfig(token_secret="deployment-specific-totp-secret-for-tests")
        return TokenParser(config.token_secret, config.token_lifetime)

    @pytest.fixture
    def token_signed_with_old_default(self) -> str:
        return TokenParser("BACKEND_AI_TOKEN_SECRET").serialize(
            "d8550bf5-4930-4afd-b581-f0da4fbe46ab"
        )

    def test_rejects_token_signed_with_old_default(
        self, token_parser: TokenParser, token_signed_with_old_default: str
    ) -> None:
        with pytest.raises(InvalidTokenError):
            token_parser.deserialize(token_signed_with_old_default)
