"""Component tests for OIDCHookPlugin (pre_auth_hook)."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import jwt as pyjwt
import pytest

from ai.backend.common.plugin.hook import Reject
from ai.backend.manager.models.user import UserStatus
from ai.backend.manager.plugin.openid.hook import OIDCHookPlugin

# ===========================================================================
# TestOIDCHookPreAuth — all cases use the real DB
# ===========================================================================


class TestOIDCHookPreAuth:
    # -----------------------------------------------------------------------
    # Scenario fixtures — each provides a "prepared request"
    # -----------------------------------------------------------------------

    @pytest.fixture
    def request_without_stoken(self, make_hook_request: Callable[..., MagicMock]) -> MagicMock:
        return make_hook_request({})

    @pytest.fixture
    async def active_user_uuid(self, insert_user: Callable[..., Any]) -> Any:
        return await insert_user(email="alice@example.com", status=UserStatus.ACTIVE)

    @pytest.fixture
    def request_with_valid_stoken(
        self,
        make_hook_request: Callable[..., MagicMock],
        active_user_uuid: uuid.UUID,
        make_stoken: Callable[..., str],
    ) -> MagicMock:
        stoken = make_stoken(active_user_uuid, "alice@example.com")
        return make_hook_request({"sToken": stoken})

    @pytest.fixture
    def request_with_invalid_stoken(self, make_hook_request: Callable[..., MagicMock]) -> MagicMock:
        now = int(time.time())
        fake_uuid = uuid.uuid4()
        stoken = pyjwt.encode(
            {"user": str(fake_uuid), "email": "alice@example.com", "exp": now + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        return make_hook_request({"sToken": stoken})

    @pytest.fixture
    def request_with_expired_stoken(
        self, make_hook_request: Callable[..., MagicMock], make_stoken: Callable[..., str]
    ) -> MagicMock:
        fake_uuid = uuid.uuid4()
        stoken = make_stoken(fake_uuid, "alice@example.com", expired=True)
        return make_hook_request({"sToken": stoken})

    @pytest.fixture
    def request_with_nonexistent_user_stoken(
        self, make_hook_request: Callable[..., MagicMock], make_stoken: Callable[..., str]
    ) -> MagicMock:
        fake_uuid = uuid.uuid4()
        stoken = make_stoken(fake_uuid, "nobody@example.com")
        return make_hook_request({"sToken": stoken})

    @pytest.fixture
    async def inactive_user_uuid(self, insert_user: Callable[..., Any]) -> Any:
        return await insert_user(email="inactive@example.com", status=UserStatus.INACTIVE)

    @pytest.fixture
    def request_with_inactive_user_stoken(
        self,
        make_hook_request: Callable[..., MagicMock],
        inactive_user_uuid: uuid.UUID,
        make_stoken: Callable[..., str],
    ) -> MagicMock:
        stoken = make_stoken(inactive_user_uuid, "inactive@example.com")
        return make_hook_request({"sToken": stoken})

    # -----------------------------------------------------------------------
    # Tests — given (fixture) -> when (call) -> then (assert)
    # -----------------------------------------------------------------------

    async def test_no_stoken_cookie_returns_none(
        self, hook_plugin: OIDCHookPlugin, request_without_stoken: MagicMock
    ) -> None:
        result = await hook_plugin.pre_auth_hook(request_without_stoken, {})
        assert result is None

    async def test_valid_stoken_active_user_returns_user(
        self,
        hook_plugin: OIDCHookPlugin,
        request_with_valid_stoken: MagicMock,
    ) -> None:
        raw_result: Any = await hook_plugin.pre_auth_hook(request_with_valid_stoken, {})
        assert raw_result is not None
        assert raw_result["email"] == "alice@example.com"
        assert raw_result["status"] == UserStatus.ACTIVE

    async def test_invalid_stoken_rejects(
        self, hook_plugin: OIDCHookPlugin, request_with_invalid_stoken: MagicMock
    ) -> None:
        with pytest.raises(Reject, match="Invalid authentication token"):
            await hook_plugin.pre_auth_hook(request_with_invalid_stoken, {})

    async def test_expired_stoken_rejects(
        self, hook_plugin: OIDCHookPlugin, request_with_expired_stoken: MagicMock
    ) -> None:
        with pytest.raises(Reject, match="Expired authentication token"):
            await hook_plugin.pre_auth_hook(request_with_expired_stoken, {})

    async def test_valid_stoken_user_not_found_rejects(
        self,
        hook_plugin: OIDCHookPlugin,
        request_with_nonexistent_user_stoken: MagicMock,
    ) -> None:
        with pytest.raises(Reject, match="user not found"):
            await hook_plugin.pre_auth_hook(request_with_nonexistent_user_stoken, {})

    async def test_valid_stoken_inactive_user_rejects(
        self,
        hook_plugin: OIDCHookPlugin,
        request_with_inactive_user_stoken: MagicMock,
    ) -> None:
        with pytest.raises(Reject, match="user is inactivated"):
            await hook_plugin.pre_auth_hook(request_with_inactive_user_stoken, {})


# ===========================================================================
# TestOIDCHookLifecycle
# ===========================================================================


class TestOIDCHookLifecycle:
    def test_get_handlers_returns_authorize(self, hook_plugin: OIDCHookPlugin) -> None:
        handlers = hook_plugin.get_handlers()
        assert len(handlers) == 1
        name, handler = handlers[0]
        assert name == "AUTHORIZE"

    async def test_init_and_cleanup(self, hook_plugin: OIDCHookPlugin) -> None:
        await hook_plugin.init()
        await hook_plugin.cleanup()

    async def test_update_plugin_config(self, hook_plugin: OIDCHookPlugin) -> None:
        new_config: dict[str, Any] = {
            "secret": "new-secret",
            "login_uri": "https://app.example.com/login",
            "openid": {
                "client_id": "new-client-id",
                "client_secret": "new-client-secret",
            },
        }
        await hook_plugin.update_plugin_config(new_config)
        assert hook_plugin.plugin_config is new_config
