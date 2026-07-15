import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any, override

import aiohttp_cors
import yarl
from aiohttp import web
from pydantic import ValidationError

from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.common.types import BackendAISchema
from ai.backend.manager.api.rest.types import CORSOptions, WebMiddleware
from ai.backend.manager.plugin.webapp import WebappPlugin

from .utils import (
    STokenData,
    get_plugin_config,
    serialize_stoken,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LoginRequestData(BackendAISchema):
    access_key: str
    secret_key: str


async def login(request: web.Request) -> web.Response:
    root_app = request.app["_root_app"]
    config_provider = root_app["_config_provider"]
    shared_config = await config_provider.legacy_etcd_config_loader.load()
    plugin_config = get_plugin_config(shared_config)

    try:
        raw_data = await request.json()
        json_data = LoginRequestData(**raw_data)
    except (json.decoder.JSONDecodeError, ValidationError, TypeError) as e:
        log.warning(
            "Invalid login request data: {}",
            repr(e),
        )
        raise web.HTTPBadRequest(reason="Invalid JSON data in request body.") from None

    token_secret = plugin_config["secret"]
    redirect_uri = yarl.URL(plugin_config["login_uri"])
    token = serialize_stoken(
        data=STokenData(
            access_key=json_data.access_key,
            secret_key=json_data.secret_key,
        ),
        secret=token_secret,
    )
    redirect_location = redirect_uri.update_query({"sToken": token})
    return web.HTTPFound(redirect_location)


async def _webapp_init(app: web.Application) -> None:
    pass


async def _webapp_shutdown(app: web.Application) -> None:
    pass


class KeypairAuthWebAppPlugin(WebappPlugin):
    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, new_plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = new_plugin_config

    @override
    async def create_app(
        self,
        cors_options: CORSOptions,
    ) -> tuple[web.Application, Sequence[WebMiddleware]]:
        app = web.Application()
        app["prefix"] = "custom-auth"
        app["api_versions"] = (4, 5, 6)
        app.on_startup.append(_webapp_init)
        app.on_shutdown.append(_webapp_shutdown)
        cors = aiohttp_cors.setup(app, defaults=cors_options)
        cors.add(app.router.add_route("POST", "/login", login))
        return app, []
