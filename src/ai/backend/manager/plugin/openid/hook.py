from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import (
    Any,
    cast,
    override,
)

import jwt
import jwt.exceptions
from aiohttp import web

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.plugin.hook import HookHandler, HookPlugin, Reject
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.user.queriers import AuthorizingUserQuerier
from ai.backend.manager.repositories.auth.repository import AuthRepository

from .config import OIDCHookConfig

log = BraceStyleAdapter(logging.getLogger(__name__))


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
        secret = self._config.secret

        stoken = params.get("stoken") or params.get("sToken") or request.cookies.get("sToken")
        if not stoken:
            log.debug(
                "AUTHORIZE_HOOK(openid): no sToken found in params or cookies. proceeded with normal auth steps"
            )
            return None
        try:
            payload = jwt.decode(stoken, secret, algorithms=["HS256"])
            user_id = UserID(uuid.UUID(payload["user"]))
            email = payload["email"]
        except jwt.ExpiredSignatureError:
            raise Reject("Expired authentication token") from None
        except (jwt.PyJWTError, KeyError, ValueError):
            raise Reject("Invalid authentication token") from None

        log.debug("AUTHORIZE_HOOK(openid): auth token {}", stoken)

        user = await auth_repository.query_user_data(AuthorizingUserQuerier(user_id))
        if user is None:
            raise Reject("user not found")
        if user.status != UserStatus.ACTIVE:
            raise Reject("user is inactivated")

        if payload.get("force", False):
            await auth_repository.invalidate_active_login_sessions(user_id)
            log.info(
                "AUTHORIZE_HOOK(openid): force-invalidated existing login sessions for {}",
                email,
            )

        log.info("AUTHORIZE_HOOK(openid): {} authenticated by auth token", email)
        return user
