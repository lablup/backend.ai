import logging
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import aiohttp_cors
import pyotp
import sqlalchemy as sa
import trafaret as t
from aiohttp import web

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.types import CORSOptions, WebMiddleware
from ai.backend.manager.api.utils import check_api_params
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.user.row import UserRow, users
from ai.backend.manager.plugin.webapp import WebappPlugin

from .config import TOTPConfig
from .exception import AuthorizationFailed, ExpiredToken, InvalidToken
from .utils import InvalidTokenError, TokenExpired, TokenParser

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@auth_required
async def initialize_otp_activation(request: web.Request) -> web.Response:
    root_app = request.app["_root_app"]
    db = root_app["_db"]
    ctx = cast(PrivateContext, request.app["context"])
    email = request["user"]["email"]
    log.info("TOTP.INITIALIZE_OTP_ACTIVATION()")
    async with db.begin_readonly() as conn:
        query = (
            sa.select(users.c.totp_activated, users.c.totp_key)
            .select_from(users)
            .where(users.c.email == email)
        )
        result = await conn.execute(query)
        user = result.fetchone()
    if user is None:
        raise InvalidAPIParameters("Email does not exist.")
    if user.totp_activated:
        raise InvalidAPIParameters("TOTP is already activated for this user.")
    new_totp_key = pyotp.random_base32()
    async with db.begin() as conn:
        update_query = (
            sa.update(users)
            .values({
                "totp_activated": False,
                "totp_key": new_totp_key,
                "totp_activated_at": sa.func.now(),
            })
            .where(users.c.email == email)
        )
        await conn.execute(update_query)
    totp = pyotp.TOTP(new_totp_key)
    totp_uri = totp.provisioning_uri(name=email, issuer_name=ctx.config.issuer)

    return web.json_response({
        "totp_key": new_totp_key,
        "totp_uri": totp_uri,
    })


@auth_required
@check_api_params(
    t.Dict({
        t.Key("otp"): t.String,
    })
)
async def finalize_otp_activation(request: web.Request, params: Any) -> web.Response:
    root_app = request.app["_root_app"]
    db = root_app["_db"]
    email = request["user"]["email"]
    log.info("TOTP.FINALIZE_OTP_ACTIVATION(otp: {})", params["otp"])

    async with db.begin_readonly() as conn:
        query = (
            sa.select(users.c.totp_activated, users.c.totp_key)
            .select_from(users)
            .where(users.c.email == email)
        )
        result = await conn.execute(query)
        user = result.fetchone()
    if user is None:
        raise InvalidAPIParameters("Email does not exist.")
    if user.totp_activated:
        raise InvalidAPIParameters("TOTP is already activated and verified for this account.")

    totp = pyotp.TOTP(user.totp_key)
    if not totp.verify(params["otp"]):
        raise AuthorizationFailed

    async with db.begin() as conn:
        update_query = (
            sa.update(users)
            .values({
                "totp_activated": True,
            })
            .where(users.c.email == email)
        )
        await conn.execute(update_query)
    return web.json_response({"success": True})


@auth_required
async def deactivate_totp(request: web.Request) -> web.Response:
    root_app = request.app["_root_app"]
    db = root_app["_db"]
    email = request["user"]["email"]
    if "email" in request.query:
        if not request["is_admin"]:
            raise GenericForbidden
        email = request.query["email"]

    log.info("TOTP.DEACTIVATE_TOTP(email: {})", email)
    async with db.begin_readonly() as conn:
        query = (
            sa.select(users.c.totp_activated, users.c.totp_key)
            .select_from(users)
            .where(users.c.email == email)
        )
        result = await conn.execute(query)
        user = result.fetchone()
    if user is None:
        raise InvalidAPIParameters("Email does not exist.")
    if not user.totp_activated:
        raise InvalidAPIParameters("TOTP is not activated for this user.")

    async with db.begin() as conn:
        update_query = (
            sa.update(users)
            .values({
                "totp_activated": False,
                "totp_key": "",
                "totp_activated_at": None,
            })
            .where(users.c.email == email)
        )
        await conn.execute(update_query)
    return web.json_response({"success": True})


@check_api_params(
    t.Dict({
        t.Key("registration_token"): t.String,
    })
)
async def initialize_anonymous_otp_activation(request: web.Request, params: Any) -> web.Response:
    root_app = request.app["_root_app"]
    db = root_app["_db"]
    ctx = cast(PrivateContext, request.app["context"])
    log.info("TOTP.INITIALIZE_OTP_ACTIVATION()")
    raw_token = params["registration_token"]
    try:
        token = ctx.token_parser.deserialize(raw_token)
    except TokenExpired:
        raise ExpiredToken() from None
    except InvalidTokenError:
        raise InvalidToken() from None

    async with db.begin_session() as db_session:
        query = sa.select(UserRow).where(UserRow.uuid == uuid.UUID(token.sub))
        user_row = cast(UserRow | None, await db_session.scalar(query))
        if user_row is None:
            raise InvalidAPIParameters(f"User does not exist. (user_id: {token.sub})")
        if user_row.totp_activated:
            raise InvalidAPIParameters("TOTP is already activated for this user.")
        email = user_row.email
        new_totp_key = pyotp.random_base32()
        user_row.totp_activated = False
        user_row.totp_key = new_totp_key
        user_row.totp_activated_at = sa.func.now()
    totp = pyotp.TOTP(new_totp_key)
    totp_uri = totp.provisioning_uri(name=email, issuer_name=ctx.config.issuer)

    return web.json_response({
        "totp_key": new_totp_key,
        "totp_uri": totp_uri,
    })


@check_api_params(
    t.Dict({
        t.Key("otp"): t.String,
        t.Key("registration_token"): t.String,
    })
)
async def finalize_anonymous_otp_activation(request: web.Request, params: Any) -> web.Response:
    root_app = request.app["_root_app"]
    db = root_app["_db"]
    ctx = cast(PrivateContext, request.app["context"])
    log.info("TOTP.FINALIZE_OTP_ACTIVATION(otp: {})", params["otp"])
    raw_token = params["registration_token"]
    try:
        token = ctx.token_parser.deserialize(raw_token)
    except TokenExpired:
        raise ExpiredToken() from None
    except InvalidTokenError:
        raise InvalidToken() from None

    async with db.begin_session() as db_session:
        query = sa.select(UserRow).where(UserRow.uuid == uuid.UUID(token.sub))
        user_row = cast(UserRow | None, await db_session.scalar(query))
        if user_row is None:
            raise InvalidAPIParameters(f"User does not exist. (user_id: {token.sub})")
        if user_row.totp_activated:
            raise InvalidAPIParameters("TOTP is already activated for this user.")
        if not user_row.totp_key:
            raise InvalidAPIParameters("TOTP key does not exist.")
        totp = pyotp.TOTP(user_row.totp_key)
        if not totp.verify(params["otp"]):
            raise AuthorizationFailed

        user_row.totp_activated = True

    return web.json_response({"success": True})


async def ping(_request: web.Request) -> web.Response:
    return web.json_response({"totp_enabled": True})


@dataclass
class PrivateContext:
    token_parser: TokenParser
    config: TOTPConfig


async def _webapp_init(app: web.Application) -> None:
    pass


async def _webapp_shutdown(app: web.Application) -> None:
    pass


class TOTPWebapp(WebappPlugin):
    require_explicit_allow = True

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        """
        Instantiate the plugin with the given initial configuration.
        """
        super().__init__(plugin_config, local_config)
        self._plugin_config = TOTPConfig(**plugin_config)
        self._token_parser = TokenParser(
            self._plugin_config.token_secret, self._plugin_config.token_lifetime
        )

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = new_plugin_config
        self._plugin_config = TOTPConfig(**self.plugin_config)
        self._token_parser.set_secret(self._plugin_config.token_secret)
        self._token_parser.set_lifetime(self._plugin_config.token_lifetime)

    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, Sequence[WebMiddleware]]:
        app = web.Application()
        self._plugin_config = TOTPConfig(**self.plugin_config)
        app["context"] = PrivateContext(
            token_parser=self._token_parser,
            config=self._plugin_config,
        )
        app["prefix"] = "totp"
        app["api_versions"] = (5,)
        app.on_startup.append(_webapp_init)
        app.on_shutdown.append(_webapp_shutdown)
        cors = aiohttp_cors.setup(app, defaults=cors_options)
        root_resource = cors.add(app.router.add_resource(r""))
        cors.add(root_resource.add_route("GET", ping))
        cors.add(root_resource.add_route("POST", initialize_otp_activation))
        cors.add(root_resource.add_route("DELETE", deactivate_totp))
        cors.add(app.router.add_route("POST", "/verify", finalize_otp_activation))
        cors.add(app.router.add_route("POST", "/anon", initialize_anonymous_otp_activation))
        cors.add(app.router.add_route("POST", "/anon/verify", finalize_anonymous_otp_activation))
        return app, []
