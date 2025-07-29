import urllib.parse
from typing import Iterable
from uuid import UUID

import aiohttp
import jwt
import yarl
from aiohttp import web
from pydantic import AnyUrl, BaseModel
from tenacity import AsyncRetrying, TryAgain, retry_if_exception_type, wait_exponential
from tenacity.stop import stop_after_attempt

from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.common.exceptions import (
    InvalidAPIParameters,
    ServerMisconfiguredError,
)
from ai.backend.appproxy.common.types import (
    CORSOptions,
    FrontendMode,
    ProxyProtocol,
    PydanticResponse,
    WebMiddleware,
)
from ai.backend.appproxy.common.types import SerializableCircuit as Circuit
from ai.backend.appproxy.common.utils import calculate_permit_hash, pydantic_api_handler

from ..config import (
    PortProxyConfig,
    TraefikPortProxyConfig,
    TraefikWildcardDomainConfig,
    WildcardDomainConfig,
)
from ..coordinator_client import get_circuit_info
from ..types import FrontendServerMode, InteractiveAppInfo, RootContext


def generate_proxy_url(
    config: PortProxyConfig
    | WildcardDomainConfig
    | TraefikPortProxyConfig
    | TraefikWildcardDomainConfig,
    protocol: str,
    circuit: Circuit,
) -> str:
    match config:
        case PortProxyConfig():
            return f"{protocol}://{config.advertised_host or config.bind_host}:{circuit.port}"
        case TraefikPortProxyConfig():
            return f"{protocol}://{config.advertised_host}:{circuit.port}"
        case WildcardDomainConfig():
            return f"{protocol}://{circuit.subdomain}{config.domain}:{config.advertised_port or config.bind_addr.port}"
        case TraefikWildcardDomainConfig():
            return f"{protocol}://{circuit.subdomain}{config.domain}:{config.advertised_port}"


async def ensure_traefik_route_set_up(traefik_api_port: int, circuit: Circuit) -> None:
    match circuit.protocol:
        case ProxyProtocol.TCP:
            proto = "tcp"
        case _:
            proto = "http"
    path = f"/api/{proto}/routers/{circuit.traefik_router_name}"

    base_url = yarl.URL("http://127.0.0.1").with_port(traefik_api_port)
    async for attempt in AsyncRetrying(
        wait=wait_exponential(multiplier=0.02, min=0.02, max=5.0),
        stop=stop_after_attempt(20),
        retry=retry_if_exception_type(TryAgain),
    ):
        with attempt:
            async with aiohttp.ClientSession(base_url=base_url) as sess:
                async with sess.get(path) as resp:
                    if resp.status == 404:
                        raise TryAgain


class ProxySetupRequestModel(BaseModel):
    token: str


class ProxySetupResponseModel(BaseModel):
    redirect: AnyUrl
    redirectURI: AnyUrl


@pydantic_api_handler(ProxySetupRequestModel)
async def setup(
    request: web.Request, params: ProxySetupRequestModel
) -> web.StreamResponse | PydanticResponse[ProxySetupResponseModel]:
    root_ctx: RootContext = request.app["_root.context"]
    jwt_body = jwt.decode(
        params.token, root_ctx.local_config.secrets.jwt_secret, algorithms=["HS256"]
    )
    requested_circuit_id = UUID(jwt_body["circuit"])

    config = root_ctx.local_config.proxy_worker
    port_config = config.port_proxy  # As a default fallback
    circuit = await get_circuit_info(root_ctx, request["request_id"], str(requested_circuit_id))

    match config.frontend_mode:
        case FrontendServerMode.TRAEFIK:
            if config.traefik is None:
                raise ServerMisconfiguredError("proxy_worker: Missing 'traefik' config section")
            match config.traefik.frontend_mode:
                case FrontendMode.PORT:
                    port_config = config.traefik.port_proxy
                    if port_config is None:
                        raise ServerMisconfiguredError(
                            "proxy_worker.traefik: Missing 'port_proxy' config section"
                        )
                case FrontendMode.WILDCARD_DOMAIN:
                    port_config = config.traefik.wildcard_domain
                    if port_config is None:
                        raise ServerMisconfiguredError(
                            "proxy_worker.traefik: Missing 'wildcard_domain' config section"
                        )
            await ensure_traefik_route_set_up(config.traefik.api_port, circuit)
        case FrontendServerMode.PORT:
            port_config = config.port_proxy
            if port_config is None:
                raise ServerMisconfiguredError(
                    "proxy_worker: Missing root-level 'port_proxy' config section"
                )
        case FrontendServerMode.WILDCARD_DOMAIN:
            port_config = config.wildcard_domain
            if port_config is None:
                raise ServerMisconfiguredError(
                    "proxy_worker: Missing root-level 'wildcard_domain' config section"
                )
        case _:
            raise ServerMisconfiguredError(
                f"proxy_worker: Invalid root-level 'frontend_mode': {config.frontend_mode}"
            )
    assert port_config is not None

    use_tls = config.tls_advertised or config.tls_listen
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
            protocol = "https" if use_tls else "http"
            response = web.HTTPPermanentRedirect(
                generate_proxy_url(port_config, protocol, circuit), headers=cors_headers
            )
            cookie_domain = None
            if circuit.frontend_mode == FrontendMode.WILDCARD_DOMAIN:
                wildcard_info = config.wildcard_domain
                if not wildcard_info:
                    raise ServerMisconfiguredError("worker:proxy-worker.wildcard-domain")
                cookie_domain = wildcard_info.domain
            response.set_cookie(
                PERMIT_COOKIE_NAME,
                calculate_permit_hash(root_ctx.local_config.permit_hash, circuit.app_info.user_id),
                domain=cookie_domain,
            )
            return response
        case ProxyProtocol.TCP:
            protocol = "tcp"
            queryparams = {
                "directTCP": "true",
                "auth": params.token,
                "proto": protocol,
                "gateway": generate_proxy_url(port_config, protocol, circuit),
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
