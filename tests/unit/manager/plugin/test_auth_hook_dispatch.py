from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.plugin.hook import FIRST_HANDLED_RUNNER, PASSED, HookPluginContext
from ai.backend.manager.data.auth.types import AuthorizingUser
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.plugin.keypair.hook import KeypairAuthHookPlugin
from ai.backend.manager.plugin.openid.hook import OIDCHookPlugin

_OPENID_SECRET = "test-openid-secret"
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
            handler_runner=FIRST_HANDLED_RUNNER,
        )

        assert hook_result.status == PASSED
        assert hook_result.result == _ACTIVE_USER
        assert hook_result.src_plugin == "openid"
