from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import (
    Any,
)

import jwt
import jwt.exceptions
import sqlalchemy as sa
from aiohttp import web

from ai.backend.common.plugin.hook import HookHandler, HookPlugin, Reject
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.login_session.enums import LoginSessionStatus
from ai.backend.manager.models.login_session.row import LoginSessionRow
from ai.backend.manager.models.user import UserStatus, users

from .config import OIDCPluginConfig

log = BraceStyleAdapter(logging.getLogger(__name__))


class OIDCHookPlugin(HookPlugin):
    require_explicit_allow = True

    # Pre-defined attributes from the base class:
    #   - local_config is populated from the manager TOML.
    #   - plugin_config is populated from the "/config/plugins/hook/openid/" etcd key
    _config: OIDCPluginConfig

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._config = OIDCPluginConfig(**plugin_config)

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config
        self._config = OIDCPluginConfig(**plugin_config)

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

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
        db = root_app["_db"]
        secret = self._config.secret

        stoken = params.get("stoken") or params.get("sToken") or request.cookies.get("sToken")
        if not stoken:
            log.debug(
                "AUTHORIZE_HOOK(openid): no sToken found in params or cookies. proceeded with normal auth steps"
            )
            return None
        try:
            payload = jwt.decode(stoken, secret, algorithms=["HS256"])
            user_uuid = payload["user"]
            email = payload["email"]
        except jwt.ExpiredSignatureError:
            raise Reject("Expired authentication token") from None
        except (jwt.PyJWTError, KeyError):
            raise Reject("Invalid authentication token") from None

        log.debug("AUTHORIZE_HOOK(openid): auth token {}", stoken)

        async with db.begin_readonly() as conn:
            query = sa.select(users).select_from(users).where(users.c.uuid == user_uuid)
            result = await conn.execute(query)
            row = result.fetchone()
            if not row:
                raise Reject("user not found")
            user = row._mapping
            if user["status"] != UserStatus.ACTIVE:
                raise Reject("user is inactivated")

        if payload.get("force", False):
            async with db.begin() as conn:
                await conn.execute(
                    sa.update(LoginSessionRow.__table__)
                    .where(
                        (LoginSessionRow.__table__.c.user_id == user_uuid)
                        & (LoginSessionRow.__table__.c.status == LoginSessionStatus.ACTIVE)
                    )
                    .values(
                        status=LoginSessionStatus.INVALIDATED,
                        invalidated_at=sa.func.now(),
                    )
                )
            log.info(
                "AUTHORIZE_HOOK(openid): force-invalidated existing login sessions for {}",
                email,
            )

        log.info("AUTHORIZE_HOOK(openid): {} authenticated by auth token", email)
        return user
