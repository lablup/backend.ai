from __future__ import annotations

from ai.backend.web.config.unified import SecurityConfig


class TestSecurityConfigCookieSecure:
    """Verify that SecurityConfig.cookie_secure defaults to True
    and can be overridden for development environments."""

    async def test_default_cookie_secure_is_true(self) -> None:
        config = SecurityConfig.model_validate({})
        assert config.cookie_secure is True

    async def test_cookie_secure_can_be_set_false(self) -> None:
        config = SecurityConfig.model_validate({"cookie_secure": False})
        assert config.cookie_secure is False

    async def test_cookie_secure_from_toml_alias(self) -> None:
        config = SecurityConfig.model_validate({"cookie-secure": False})
        assert config.cookie_secure is False
