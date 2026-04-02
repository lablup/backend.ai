"""Component tests for OIDCHookPlugin (pre_auth_hook)."""

from __future__ import annotations

import time
import uuid

import jwt as pyjwt
import pytest
import pytest_asyncio

from ai.backend.common.plugin.hook import Reject
from ai.backend.manager.data.user.types import UserStatus

# ===========================================================================
# TestOIDCHookPreAuth — all cases use the real DB
# ===========================================================================


class TestOIDCHookPreAuth:
    # -----------------------------------------------------------------------
    # Scenario fixtures — each provides a "prepared request"
    # -----------------------------------------------------------------------

    @pytest.fixture
    def request_without_stoken(self, make_hook_request):
        return make_hook_request({})

    @pytest_asyncio.fixture
    async def active_user_uuid(self, insert_user):
        return await insert_user(email="alice@example.com", status=UserStatus.ACTIVE)

    @pytest.fixture
    def request_with_valid_stoken(self, make_hook_request, active_user_uuid, make_stoken):
        stoken = make_stoken(active_user_uuid, "alice@example.com")
        return make_hook_request({"sToken": stoken})

    @pytest.fixture
    def request_with_invalid_stoken(self, make_hook_request):
        now = int(time.time())
        fake_uuid = uuid.uuid4()
        stoken = pyjwt.encode(
            {"user": str(fake_uuid), "email": "alice@example.com", "exp": now + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        return make_hook_request({"sToken": stoken})

    @pytest.fixture
    def request_with_expired_stoken(self, make_hook_request, make_stoken):
        fake_uuid = uuid.uuid4()
        stoken = make_stoken(fake_uuid, "alice@example.com", expired=True)
        return make_hook_request({"sToken": stoken})

    @pytest.fixture
    def request_with_nonexistent_user_stoken(self, make_hook_request, make_stoken):
        fake_uuid = uuid.uuid4()
        stoken = make_stoken(fake_uuid, "nobody@example.com")
        return make_hook_request({"sToken": stoken})

    @pytest_asyncio.fixture
    async def inactive_user_uuid(self, insert_user):
        return await insert_user(email="inactive@example.com", status=UserStatus.INACTIVE)

    @pytest.fixture
    def request_with_inactive_user_stoken(
        self,
        make_hook_request,
        inactive_user_uuid,
        make_stoken,
    ):
        stoken = make_stoken(inactive_user_uuid, "inactive@example.com")
        return make_hook_request({"sToken": stoken})

    # -----------------------------------------------------------------------
    # Tests — given (fixture) -> when (call) -> then (assert)
    # -----------------------------------------------------------------------

    async def test_no_stoken_cookie_returns_none(self, hook_plugin, request_without_stoken):
        result = await hook_plugin.pre_auth_hook(request_without_stoken, {})
        assert result is None

    async def test_valid_stoken_active_user_returns_user(
        self,
        hook_plugin,
        request_with_valid_stoken,
    ):
        result = await hook_plugin.pre_auth_hook(request_with_valid_stoken, {})
        assert result is not None
        assert result["email"] == "alice@example.com"
        assert result["status"] == UserStatus.ACTIVE

    async def test_invalid_stoken_rejects(self, hook_plugin, request_with_invalid_stoken):
        with pytest.raises(Reject, match="Invalid authentication token"):
            await hook_plugin.pre_auth_hook(request_with_invalid_stoken, {})

    async def test_expired_stoken_rejects(self, hook_plugin, request_with_expired_stoken):
        with pytest.raises(Reject, match="Invalid authentication token"):
            await hook_plugin.pre_auth_hook(request_with_expired_stoken, {})

    async def test_valid_stoken_user_not_found_rejects(
        self,
        hook_plugin,
        request_with_nonexistent_user_stoken,
    ):
        with pytest.raises(Reject, match="user not found"):
            await hook_plugin.pre_auth_hook(request_with_nonexistent_user_stoken, {})

    async def test_valid_stoken_inactive_user_rejects(
        self,
        hook_plugin,
        request_with_inactive_user_stoken,
    ):
        with pytest.raises(Reject, match="user is inactivated"):
            await hook_plugin.pre_auth_hook(request_with_inactive_user_stoken, {})


# ===========================================================================
# TestOIDCHookLifecycle
# ===========================================================================


class TestOIDCHookLifecycle:
    def test_get_handlers_returns_authorize(self, hook_plugin):
        handlers = hook_plugin.get_handlers()
        assert len(handlers) == 1
        name, handler = handlers[0]
        assert name == "AUTHORIZE"

    async def test_init_and_cleanup(self, hook_plugin):
        await hook_plugin.init()
        await hook_plugin.cleanup()

    async def test_update_plugin_config(self, hook_plugin):
        new_config = {"secret": "new-secret", "openid": {}}
        await hook_plugin.update_plugin_config(new_config)
        assert hook_plugin.plugin_config is new_config
