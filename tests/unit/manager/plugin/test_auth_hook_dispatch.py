from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.plugin.hook import FIRST_COMPLETED, PASSED, REJECTED
from ai.backend.common.plugin.hook_context import HookPluginContext
from ai.backend.manager.data.auth.types import AuthorizingUser
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.plugin.keypair.hook import KeypairAuthHookPlugin
from ai.backend.manager.plugin.keypair.utils import STokenData, serialize_stoken
from ai.backend.manager.plugin.openid.hook import OIDCHookPlugin

_OPENID_SECRET = "test-openid-secret"
_KEYPAIR_SECRET = "test-keypair-secret"
_ACTIVE_USER = AuthorizingUser(
    uuid=UserID(uuid.UUID(int=1)),
    username="alice",
    email="alice@example.com",
    status=UserStatus.ACTIVE,
    role=UserRole.USER,
    resource_policy="default",
    password_changed_at=None,
    totp_activated=False,
    totp_key=None,
)


@dataclass(frozen=True)
class _CookieLoginWithKeypairAndOpenID:
    ctx: HookPluginContext
    request: MagicMock


class TestAuthorizeAfterKeypairReturnsNone:
    @pytest.fixture
    def cookie_login_with_keypair_and_openid(self) -> _CookieLoginWithKeypairAndOpenID:
        openid_stoken = jwt.encode(
            {
                "user": str(_ACTIVE_USER.uuid),
                "email": _ACTIVE_USER.email,
                "exp": int(time.time()) + 3600,
            },
            _OPENID_SECRET,
            algorithm="HS256",
        )
        config_provider = MagicMock()
        config_provider.legacy_etcd_config_loader.load = AsyncMock(return_value={})
        auth_repository = MagicMock()
        auth_repository.query_user_data = AsyncMock(return_value=_ACTIVE_USER)
        request = MagicMock()
        request.cookies = {"sToken": openid_stoken}
        request.json = AsyncMock(return_value={})
        request.app = {
            "_root_app": {
                "_auth_repository": auth_repository,
                "_config_provider": config_provider,
            }
        }
        ctx = HookPluginContext(MagicMock(spec=AsyncEtcd), {})
        ctx.plugins = {
            "auth_keypair": KeypairAuthHookPlugin({}, {}),
            "openid": OIDCHookPlugin({"secret": _OPENID_SECRET}, {}),
        }
        return _CookieLoginWithKeypairAndOpenID(ctx=ctx, request=request)

    async def test_openid_authenticates_the_cookie(
        self, cookie_login_with_keypair_and_openid: _CookieLoginWithKeypairAndOpenID
    ) -> None:
        hook_result = await cookie_login_with_keypair_and_openid.ctx.dispatch(
            "AUTHORIZE",
            (cookie_login_with_keypair_and_openid.request, {"stoken": "", "sToken": ""}),
            return_when=FIRST_COMPLETED,
        )

        assert hook_result.status == PASSED
        assert hook_result.result == _ACTIVE_USER
        assert hook_result.src_plugin == "openid"


@dataclass(frozen=True)
class _ParamsLoginWithKeypairAndOpenID:
    ctx: HookPluginContext
    request: MagicMock


class TestAuthorizeWithInitializedKeypair:
    @pytest.fixture
    async def params_login_with_keypair_and_openid(self) -> _ParamsLoginWithKeypairAndOpenID:
        auth_repository = MagicMock()
        auth_repository.query_user_data = AsyncMock(return_value=_ACTIVE_USER)
        signing_material = MagicMock(secret_key="keypair-secret-key", user_id=_ACTIVE_USER.uuid)
        auth_repository.get_keypair_signing_material = AsyncMock(return_value=signing_material)
        request = MagicMock()
        request.cookies = {}
        request.json = AsyncMock(return_value={})
        request.app = {"_root_app": {"_auth_repository": auth_repository}}
        keypair_plugin = KeypairAuthHookPlugin({}, {})
        await keypair_plugin.init({"webapp": {"keypair_auth": {"secret": _KEYPAIR_SECRET}}})
        ctx = HookPluginContext(MagicMock(spec=AsyncEtcd), {})
        ctx.plugins = {
            "auth_keypair": keypair_plugin,
            "openid": OIDCHookPlugin({"secret": _OPENID_SECRET}, {}),
        }
        return _ParamsLoginWithKeypairAndOpenID(ctx=ctx, request=request)

    async def test_openid_authenticates_an_openid_stoken_in_params(
        self, params_login_with_keypair_and_openid: _ParamsLoginWithKeypairAndOpenID
    ) -> None:
        openid_stoken = jwt.encode(
            {
                "user": str(_ACTIVE_USER.uuid),
                "email": _ACTIVE_USER.email,
                "exp": int(time.time()) + 3600,
            },
            _OPENID_SECRET,
            algorithm="HS256",
        )

        hook_result = await params_login_with_keypair_and_openid.ctx.dispatch(
            "AUTHORIZE",
            (
                params_login_with_keypair_and_openid.request,
                {"stoken": openid_stoken, "sToken": openid_stoken},
            ),
            return_when=FIRST_COMPLETED,
        )

        assert hook_result.status == PASSED
        assert hook_result.result == _ACTIVE_USER
        assert hook_result.src_plugin == "openid"

    async def test_keypair_rejects_a_keypair_stoken_with_a_wrong_signature(
        self, params_login_with_keypair_and_openid: _ParamsLoginWithKeypairAndOpenID
    ) -> None:
        keypair_stoken = "BackendAI signMethod=HMAC-SHA256, credential=AKIATEST:deadbeef"

        hook_result = await params_login_with_keypair_and_openid.ctx.dispatch(
            "AUTHORIZE",
            (
                params_login_with_keypair_and_openid.request,
                {"stoken": keypair_stoken, "sToken": keypair_stoken},
            ),
            return_when=FIRST_COMPLETED,
        )

        assert hook_result.status == REJECTED
        assert hook_result.src_plugin == "auth_keypair"

    async def test_keypair_rejects_an_expired_keypair_stoken(
        self, params_login_with_keypair_and_openid: _ParamsLoginWithKeypairAndOpenID
    ) -> None:
        expired_stoken = serialize_stoken(
            STokenData(access_key="AKIATEST"), _KEYPAIR_SECRET, ttl_seconds=-3600
        )

        hook_result = await params_login_with_keypair_and_openid.ctx.dispatch(
            "AUTHORIZE",
            (
                params_login_with_keypair_and_openid.request,
                {"stoken": expired_stoken, "sToken": expired_stoken},
            ),
            return_when=FIRST_COMPLETED,
        )

        assert hook_result.status == REJECTED
        assert hook_result.src_plugin == "auth_keypair"

    async def test_keypair_rejects_a_keypair_stoken_signed_with_another_secret(
        self, params_login_with_keypair_and_openid: _ParamsLoginWithKeypairAndOpenID
    ) -> None:
        forged_stoken = serialize_stoken(STokenData(access_key="AKIATEST"), "another-secret")

        hook_result = await params_login_with_keypair_and_openid.ctx.dispatch(
            "AUTHORIZE",
            (
                params_login_with_keypair_and_openid.request,
                {"stoken": forged_stoken, "sToken": forged_stoken},
            ),
            return_when=FIRST_COMPLETED,
        )

        assert hook_result.status == REJECTED
        assert hook_result.src_plugin == "auth_keypair"


class TestKeypairHookStartup:
    async def test_missing_secret_fails_plugin_loading(self) -> None:
        etcd = MagicMock(spec=AsyncEtcd)
        etcd.get_prefix = AsyncMock(return_value={})
        ctx = HookPluginContext(etcd, {})

        with (
            patch.object(
                HookPluginContext,
                "discover_plugins",
                return_value=[("auth_keypair", KeypairAuthHookPlugin)],
            ),
            pytest.raises(BackendAISchemaValidationFailed),
        ):
            await ctx.init(context={"webapp": {"openid": {}}}, allowlist={"auth_keypair"})
