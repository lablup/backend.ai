from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.manager.plugin.totp.config import TOTPConfig


class TestTOTPConfigTokenSecret:
    @pytest.mark.parametrize(
        "plugin_config",
        [{}, {"token_secret": ""}, {"token_secret": "s" * 31}],
    )
    def test_rejects_missing_or_short_secret(self, plugin_config: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            TOTPConfig(**plugin_config)

    @pytest.mark.parametrize("length", [32, 33])
    def test_accepts_secret_with_at_least_32_characters(self, length: int) -> None:
        secret = "s" * length

        config = TOTPConfig(token_secret=secret)

        assert config.token_secret == secret
