from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.web.session import AbstractStorage
from ai.backend.web.config.unified import CookieSameSite, SecurityConfig
from ai.backend.web.server import redis_ctx


class TestCookieSameSiteConfig:
    def test_default_is_lax(self) -> None:
        assert SecurityConfig.model_validate({}).cookie_samesite is CookieSameSite.LAX

    @pytest.mark.parametrize("value", list(CookieSameSite))
    def test_accepts_each_value_from_toml_alias(self, value: CookieSameSite) -> None:
        config = SecurityConfig.model_validate({"cookie-samesite": value.value})
        assert config.cookie_samesite is value

    def test_rejects_unknown_value(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            SecurityConfig.model_validate({"cookie-samesite": "Sometimes"})

    def test_none_without_secure_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match="requires cookie-secure"):
            SecurityConfig.model_validate({"cookie-samesite": "None", "cookie-secure": False})

    @pytest.mark.parametrize("value", [CookieSameSite.STRICT, CookieSameSite.LAX])
    def test_other_values_allow_insecure_cookie(self, value: CookieSameSite) -> None:
        config = SecurityConfig.model_validate({
            "cookie-samesite": value.value,
            "cookie-secure": False,
        })
        assert config.cookie_samesite is value


class TestSessionCookieAttribute:
    @pytest.fixture
    def setup_session(self) -> Iterator[MagicMock]:
        with (
            patch("ai.backend.web.server.ValkeySessionClient.create", AsyncMock()),
            patch("ai.backend.web.server.setup_session") as setup_session,
        ):
            yield setup_session

    @pytest.mark.parametrize("value", list(CookieSameSite))
    async def test_redis_ctx_applies_configured_samesite(
        self,
        setup_session: MagicMock,
        value: CookieSameSite,
    ) -> None:
        config = MagicMock()
        config.session.flush_on_startup = False
        config.session.max_age = 3600
        config.security = SecurityConfig.model_validate({"cookie-samesite": value.value})

        async with redis_ctx(config, web.Application(), 0):
            pass

        storage: AbstractStorage = setup_session.call_args.args[1]
        response = web.Response()
        storage.save_cookie(response, "session-id", max_age=3600)
        cookie = response.cookies["AIOHTTP_SESSION"]
        assert cookie["samesite"] == value.value
        assert cookie["secure"] is True
