from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.manager.plugin.totp.config import TOTPConfig


class TestTOTPConfigTokenSecret:
    @pytest.mark.parametrize("plugin_config", [{}, {"token_secret": ""}])
    def test_refuses_config_without_secret(self, plugin_config: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            TOTPConfig(**plugin_config)
