import urllib.parse
from logging import LoggerAdapter
from typing import Iterable
from uuid import UUID

import jwt
from aiohttp import web
from pydantic import AnyUrl, BaseModel

from ..config import ServerConfig
from ..defs import RootContext
from ..exceptions import (
    InvalidAPIParameters,
)
from ..types import (
    PERMIT_COOKIE_NAME,
    Circuit,
    CORSOptions,
    InteractiveAppInfo,
    ProxyProtocol,
    PydanticResponse,
    WebMiddleware,
)
from ..utils import calculate_permit_hash
from .utils import pydantic_api_handler


def generate_proxy_url(local_config: ServerConfig, protocol: str, circuit: Circuit) -> str:
    config = local_config.wsproxy
    if config.advertised_proxy_port_range:
        idx = config.bind_proxy_port_range.index(circuit.port)
        port = config.advertised_proxy_port_range[idx]
    else:
        port = circuit.port
    return f"{protocol}://{config.advertised_host}:{port}"


class ProxySetupRequestModel(BaseModel):
    token: str


class ProxySetupResponseModel(BaseModel):
    redirect: AnyUrl
    redirectURI: AnyUrl


@pydantic_api_handler(ProxySetupRequestModel)
async def setup(
    request: web.Request, params: ProxySetupRequestModel
) -> web.StreamResponse | PydanticResponse[ProxySetupResponseModel]:
    log: LoggerAdapter = request["log"]

    try:
        root_ctx: RootContext = request.app["_root.context"]
        jwt_body = jwt.decode(
            params.token, root_ctx.local_config.wsproxy.jwt_encrypt_key, algorithms=["HS256"]
        )
        requested_circuit_id = UUID(jwt_body["circuit"])

        circuit = root_ctx.proxy_frontend.get_circuit_by_id(requested_circuit_id)

        if not isinstance(circuit.app_info, InteractiveAppInfo):
            raise InvalidAPIParameters("E20011: Not supported for inference apps")

        # Web browsers block redirect between cross-origins if Access-Control-Allow-Origin value is set to a concrete Origin instead of wildcard;
        # Hence we need to send "*" as allowed origin manually, instead of benefiting from aiohttp-cors
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "*",
        }
        match circuit.protocol:
            case ProxyProtocol.HTTP:
                protocol = "http"
                response = web.HTTPPermanentRedirect(
                    generate_proxy_url(root_ctx.local_config, protocol, circuit),
                    headers=cors_headers,
                )
                response.set_cookie(
                    PERMIT_COOKIE_NAME,
                    calculate_permit_hash(
                        root_ctx.local_config.wsproxy.permit_hash_key, circuit.app_info.user_id
                    ),
                )
                return response
            case ProxyProtocol.TCP:
                protocol = "tcp"
                queryparams = {
                    "directTCP": "true",
                    "auth": params.token,
                    "proto": protocol,
                    "gateway": generate_proxy_url(root_ctx.local_config, protocol, circuit),
                }
                if jwt_body["redirect"]:
                    return web.HTTPPermanentRedirect(
                        f"http://localhost:45678/start?{urllib.parse.urlencode(queryparams)}",
                        headers=cors_headers,
                    )
                else:
                    return PydanticResponse(
                        ProxySetupResponseModel(
                            redirect=AnyUrl(
                                f"http://localhost:45678/start?{urllib.parse.urlencode(queryparams)}"
                            ),
                            redirectURI=AnyUrl(
                                f"http://localhost:45678/start?{urllib.parse.urlencode(queryparams)}"
                            ),
                        ),
                        headers=cors_headers,
                    )
            case _:
                raise InvalidAPIParameters("E20002: Protocol not available as interactive app")
    except:
        log.exception("")
        raise


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "setup"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    add_route = app.router.add_route
    add_route("GET", "", setup)
    return app, []
