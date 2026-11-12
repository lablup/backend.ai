from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import jwt
import pyotp
import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.plugin.hook import (
    FIRST_HANDLED_RUNNER,
    PASSED,
    REJECTED,
    HookPluginContext,
    HookResults,
)
from ai.backend.manager.data.auth.types import AuthorizingUser
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.plugin.keypair.hook import KeypairAuthHookPlugin
from ai.backend.manager.plugin.openid.hook import OIDCHookPlugin
from ai.backend.manager.plugin.totp.hook import TOTPHook

_OPENID_SECRET = "test-openid-secret"
_TOTP_KEY = "JBSWY3DPEHPK3PXP"
_TOTP_TOKEN_SECRET = "totp-registration-token-secret-for-tests"
_ACTIVE_USER_WITH_TOTP = AuthorizingUser(
    uuid=UserID(uuid.UUID(int=1)),
    username="alice",
    email="alice@example.com",
    status=UserStatus.ACTIVE,
    role=UserRole.USER,
    resource_policy="default",
    password_changed_at=None,
    totp_activated=True,
    totp_key=_TOTP_KEY,
)
_INACTIVE_USER = replace(_ACTIVE_USER_WITH_TOTP, status=UserStatus.INACTIVE)
_HOOK_PARAMS_WITHOUT_TOKEN: Mapping[str, str] = {"stoken": "", "sToken": ""}


def _openid_stoken_expiring_in(seconds: int) -> str:
    return jwt.encode(
        {
            "user": str(_ACTIVE_USER_WITH_TOTP.uuid),
            "email": _ACTIVE_USER_WITH_TOTP.email,
            "exp": int(time.time()) + seconds,
        },
        _OPENID_SECRET,
        algorithm="HS256",
    )


def _request_with_cookies(
    cookies: Mapping[str, str], user_in_repository: AuthorizingUser = _ACTIVE_USER_WITH_TOTP
) -> MagicMock:
    config_provider = MagicMock()
    config_provider.legacy_etcd_config_loader.load = AsyncMock(return_value={})
    auth_repository = MagicMock()
    auth_repository.query_user_data = AsyncMock(return_value=user_in_repository)
    request = MagicMock()
    request.cookies = cookies
    request.json = AsyncMock(return_value={})
    request.app = {
        "_root_app": {
            "_auth_repository": auth_repository,
            "_config_provider": config_provider,
        }
    }
    return request


@dataclass(frozen=True)
class _AuthorizeDispatchCase:
    cookies: Mapping[str, str]
    expected_status: HookResults
    expected_result: AuthorizingUser | None
    expected_src_plugin: str | list[str]
    user_in_repository: AuthorizingUser = _ACTIVE_USER_WITH_TOTP


@dataclass(frozen=True)
class _KeypairAndOpenIDDispatch:
    ctx: HookPluginContext
    request: MagicMock


class TestAuthorizeAfterKeypairReturnsNone:
    @pytest.fixture
    def keypair_and_openid_dispatch(
        self, case: _AuthorizeDispatchCase
    ) -> _KeypairAndOpenIDDispatch:
        ctx = HookPluginContext(MagicMock(spec=AsyncEtcd), {})
        ctx.plugins = {
            "auth_keypair": KeypairAuthHookPlugin({}, {}),
            "openid": OIDCHookPlugin({"secret": _OPENID_SECRET}, {}),
        }
        return _KeypairAndOpenIDDispatch(
            ctx=ctx,
            request=_request_with_cookies(case.cookies, case.user_in_repository),
        )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _AuthorizeDispatchCase(
                    cookies={"sToken": _openid_stoken_expiring_in(3600)},
                    expected_status=PASSED,
                    expected_result=_ACTIVE_USER_WITH_TOTP,
                    expected_src_plugin="openid",
                ),
                id="openid_authenticates_the_cookie",
            ),
            pytest.param(
                _AuthorizeDispatchCase(
                    cookies={"sToken": _openid_stoken_expiring_in(3600)},
                    user_in_repository=_INACTIVE_USER,
                    expected_status=REJECTED,
                    expected_result=None,
                    expected_src_plugin="openid",
                ),
                id="openid_rejects_the_inactive_user",
            ),
            pytest.param(
                _AuthorizeDispatchCase(
                    cookies={"sToken": _openid_stoken_expiring_in(-3600)},
                    expected_status=PASSED,
                    expected_result=None,
                    expected_src_plugin=["auth_keypair", "openid"],
                ),
                id="expired_cookie_leaves_the_login_unhandled",
            ),
            pytest.param(
                _AuthorizeDispatchCase(
                    cookies={"sToken": "not-a-jwt"},
                    expected_status=PASSED,
                    expected_result=None,
                    expected_src_plugin=["auth_keypair", "openid"],
                ),
                id="invalid_cookie_leaves_the_login_unhandled",
            ),
            pytest.param(
                _AuthorizeDispatchCase(
                    cookies={},
                    expected_status=PASSED,
                    expected_result=None,
                    expected_src_plugin=["auth_keypair", "openid"],
                ),
                id="no_token_leaves_the_login_unhandled",
            ),
        ],
    )
    async def test_dispatch_result(
        self, case: _AuthorizeDispatchCase, keypair_and_openid_dispatch: _KeypairAndOpenIDDispatch
    ) -> None:
        hook_result = await keypair_and_openid_dispatch.ctx.dispatch(
            "AUTHORIZE",
            (keypair_and_openid_dispatch.request, _HOOK_PARAMS_WITHOUT_TOKEN),
            handler_runner=FIRST_HANDLED_RUNNER,
        )

        assert hook_result.status == case.expected_status
        assert hook_result.result == case.expected_result
        assert hook_result.src_plugin == case.expected_src_plugin


@dataclass(frozen=True)
class _PostAuthorizeDispatchCase:
    make_otp: Callable[[], str]
    expected_status: HookResults
    expected_src_plugin: str | list[str]


@dataclass(frozen=True)
class _KeypairAndTotpDispatch:
    ctx: HookPluginContext
    request: MagicMock
    post_authorize_params: Mapping[str, Any]


class TestPostAuthorizeAfterKeypairReturnsNone:
    @pytest.fixture
    def keypair_and_totp_dispatch(
        self, case: _PostAuthorizeDispatchCase
    ) -> _KeypairAndTotpDispatch:
        ctx = HookPluginContext(MagicMock(spec=AsyncEtcd), {})
        ctx.plugins = {
            "auth_keypair": KeypairAuthHookPlugin({}, {}),
            "totp": TOTPHook({"token_secret": _TOTP_TOKEN_SECRET}, {}),
        }
        return _KeypairAndTotpDispatch(
            ctx=ctx,
            request=_request_with_cookies({}),
            post_authorize_params={"otp": case.make_otp()},
        )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _PostAuthorizeDispatchCase(
                    make_otp=lambda: pyotp.TOTP(_TOTP_KEY).now(),
                    expected_status=PASSED,
                    expected_src_plugin=["totp"],
                ),
                id="totp_accepts_the_current_otp",
            ),
            pytest.param(
                _PostAuthorizeDispatchCase(
                    make_otp=lambda: "not-an-otp",
                    expected_status=REJECTED,
                    expected_src_plugin="totp",
                ),
                id="totp_rejects_a_wrong_otp",
            ),
        ],
    )
    async def test_totp_decides_after_keypair_returned_none(
        self, case: _PostAuthorizeDispatchCase, keypair_and_totp_dispatch: _KeypairAndTotpDispatch
    ) -> None:
        authorize_result = await keypair_and_totp_dispatch.ctx.dispatch(
            "AUTHORIZE",
            (keypair_and_totp_dispatch.request, _HOOK_PARAMS_WITHOUT_TOKEN),
            handler_runner=FIRST_HANDLED_RUNNER,
        )
        post_authorize_result = await keypair_and_totp_dispatch.ctx.dispatch(
            "POST_AUTHORIZE",
            (
                keypair_and_totp_dispatch.request,
                keypair_and_totp_dispatch.post_authorize_params,
                _ACTIVE_USER_WITH_TOTP,
                {},
            ),
            handler_runner=FIRST_HANDLED_RUNNER,
        )

        assert authorize_result.status == PASSED
        assert authorize_result.result is None
        assert post_authorize_result.status == case.expected_status
        assert post_authorize_result.result is None
        assert post_authorize_result.src_plugin == case.expected_src_plugin
