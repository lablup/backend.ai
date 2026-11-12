from __future__ import annotations

import logging
import uuid
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import (
    Any,
    cast,
    override,
)

import jwt
import jwt.exceptions
from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.plugin.hook import HookHandler, HookPlugin, Reject
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.user.queriers import AuthorizingUserQuerier
from ai.backend.manager.repositories.auth.repository import AuthRepository

from .config import OIDCHookConfig
from .exceptions import ExpiredOpenIDSToken, InvalidOpenIDSToken, OpenIDSTokenVerificationFailed

log = StructuredLogger(logging.getLogger(__name__))


@dataclass(frozen=True)
class _OpenIDSTokenClaims:
    user_id: UserID
    email: str
    force: bool


@dataclass(frozen=True)
class _OpenIDSToken(metaclass=ABCMeta):
    value: str

    @abstractmethod
    def decode_to_claims(self, secret: str) -> _OpenIDSTokenClaims | None:
        raise NotImplementedError

    def _decode_claims(self, secret: str) -> _OpenIDSTokenClaims:
        try:
            payload = jwt.decode(self.value, secret, algorithms=["HS256"])
            return _OpenIDSTokenClaims(
                user_id=UserID(uuid.UUID(payload["user"])),
                email=payload["email"],
                force=payload.get("force", False),
            )
        except jwt.ExpiredSignatureError:
            raise ExpiredOpenIDSToken() from None
        except (jwt.PyJWTError, KeyError, ValueError):
            raise InvalidOpenIDSToken() from None


class _OpenIDSTokenInParams(_OpenIDSToken):
    """The caller sends this token to log in with it, so a token failing verification rejects the login."""

    @override
    def decode_to_claims(self, secret: str) -> _OpenIDSTokenClaims:
        return self._decode_claims(secret)


class _OpenIDSTokenInCookie(_OpenIDSToken):
    """
    Only a client calling the manager directly sends this cookie without the token in params. It may be left
    from an earlier login and come with a password login that auth_keypair leaves unhandled, so a token
    failing verification leaves the login to password verification instead of rejecting it.
    """

    @override
    def decode_to_claims(self, secret: str) -> _OpenIDSTokenClaims | None:
        try:
            return self._decode_claims(secret)
        except OpenIDSTokenVerificationFailed as e:
            log.debug(
                "openid auth cookie failed verification, proceeding with password verification",
                reason=e.reason,
            )
            return None


class OIDCHookPlugin(HookPlugin):
    require_explicit_allow = True

    # Pre-defined attributes from the base class:
    #   - local_config is populated from the manager TOML.
    #   - plugin_config is populated from the "/config/plugins/hook/openid/" etcd key
    _config: OIDCHookConfig

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._config = OIDCHookConfig(**plugin_config)

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config
        self._config = OIDCHookConfig(**plugin_config)

    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    def get_handlers(self) -> Sequence[tuple[str, HookHandler]]:
        return [
            ("AUTHORIZE", self.pre_auth_hook),
        ]

    async def pre_auth_hook(
        self,
        request: web.Request,
        params: Mapping[str, Any],
    ) -> Any:
        root_app = request.app["_root_app"]
        auth_repository = cast(AuthRepository, root_app["_auth_repository"])

        stoken = self._find_stoken(request, params)
        if stoken is None:
            log.debug("openid auth token not found, proceeding with normal auth")
            return None
        stoken_claims = stoken.decode_to_claims(self._config.secret)
        if stoken_claims is None:
            return None

        log.debug("openid auth token decoded", user_id=stoken_claims.user_id)

        user = await auth_repository.query_user_data(AuthorizingUserQuerier(stoken_claims.user_id))
        if user is None:
            raise Reject("user not found")
        if user.status != UserStatus.ACTIVE:
            raise Reject("user is inactivated")

        if stoken_claims.force:
            invalidated_tokens = await auth_repository.invalidate_active_login_sessions(
                stoken_claims.user_id
            )
            valkey_session = cast(ValkeySessionClient, root_app["_valkey_session"])
            await valkey_session.delete_login_sessions(invalidated_tokens)
            log.trace("openid login sessions force-invalidated", user_email=stoken_claims.email)

        log.trace("openid user authenticated by auth token", user_email=stoken_claims.email)
        return user

    def _find_stoken(self, request: web.Request, params: Mapping[str, Any]) -> _OpenIDSToken | None:
        stoken_in_params = params.get("stoken") or params.get("sToken")
        if stoken_in_params:
            return _OpenIDSTokenInParams(stoken_in_params)
        stoken_in_cookie = request.cookies.get("sToken")
        if stoken_in_cookie:
            return _OpenIDSTokenInCookie(stoken_in_cookie)
        return None
