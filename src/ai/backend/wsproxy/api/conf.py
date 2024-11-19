from logging import LoggerAdapter
from typing import Iterable

import aiohttp_cors
import jwt
from aiohttp import web
from pydantic import BaseModel

from ..defs import RootContext
from ..types import CORSOptions, PydanticResponse, WebMiddleware
from ..utils import ensure_json_serializable
from .types import ConfRequestModel
from .utils import pydantic_api_handler


class TokenResponseModel(BaseModel):
    token: str


@pydantic_api_handler(ConfRequestModel)
async def conf_v2(
    request: web.Request, params: ConfRequestModel
) -> PydanticResponse[TokenResponseModel]:
    """
    Generates and returns a token which will be used as an authentication credential for
     /v2/proxy/{token}/{session}/add request.
    """
    log: LoggerAdapter = request["log"]

    root_ctx: RootContext = request.app["_root.context"]

    assert params.session.id and params.session.access_key, "Not meant for inference apps"

    token = jwt.encode(
        ensure_json_serializable({
            "login_session_token": params.login_session_token,
            "kernel_host": params.kernel_host,
            "kernel_port": params.kernel_port,
            "session_id": params.session.id,
            "user_uuid": params.session.user_uuid,
            "group_id": params.session.group_id,
            "access_key": params.session.access_key,
            "domain_name": params.session.domain_name,
        }),
        root_ctx.local_config.wsproxy.jwt_encrypt_key,
    )
    log.debug("built token with body {}", params.model_dump())

    return PydanticResponse(TokenResponseModel(token=token))


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v2/conf"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("POST", conf_v2))
    return app, []
