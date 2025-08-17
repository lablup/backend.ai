import logging
import uuid
from typing import Iterable

import aiohttp_cors
from aiohttp import web
from pydantic import BaseModel

from ai.backend.appproxy.common.exceptions import AuthorizationFailed
from ai.backend.appproxy.common.types import CORSOptions, PydanticResponse, WebMiddleware
from ai.backend.appproxy.common.utils import pydantic_api_handler
from ai.backend.appproxy.coordinator.api.types import ConfRequestModel
from ai.backend.appproxy.coordinator.types import RootContext
from ai.backend.logging import BraceStyleAdapter

from ..models import Token

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


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

    root_ctx: RootContext = request.app["_root.context"]
    if not root_ctx.local_config.proxy_coordinator.allow_unauthorized_configure_request:
        token_to_evaluate = request.headers.get("X-BackendAI-Token")
        if token_to_evaluate != root_ctx.local_config.secrets.api_secret:
            raise AuthorizationFailed("Unauthorized access")

    assert params.session.id and params.session.access_key, "Not meant for inference apps"

    async with root_ctx.db.begin_session() as sess:
        token_id = uuid.uuid4()
        token = Token.create(
            token_id,
            params.login_session_token,
            params.kernel_host,
            params.kernel_port,
            params.session.id,
            params.session.user_uuid,
            params.session.group_id,
            params.session.access_key,
            params.session.domain_name,
        )
        sess.add(token)
        log.debug("build token with body {}", params.model_dump())

        return PydanticResponse(TokenResponseModel(token=str(token_id)))


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
