import urllib.parse
from logging import LoggerAdapter
from typing import Annotated, Iterable
from uuid import UUID

import aiohttp_cors
import jwt
from aiohttp import web
from pydantic import AnyUrl, BaseModel, Field

from ..defs import RootContext
from ..exceptions import (
    GenericForbidden,
    InvalidCredentials,
    ObjectNotFound,
)
from ..registry import add_circuit
from ..types import (
    AppMode,
    Circuit,
    CORSOptions,
    ProxyProtocol,
    PydanticResponse,
    RouteInfo,
    SessionConfig,
    WebMiddleware,
)
from ..utils import is_permit_valid, mime_match
from .types import ConfRequestModel, StubResponseModel
from .utils import pydantic_api_handler, pydantic_api_response_handler


class AddRequestModel(BaseModel):
    app: str
    protocol: ProxyProtocol
    envs: Annotated[dict[str, str | int | None], Field(default={})]
    args: Annotated[str | None, Field(default=None)]
    open_to_public: Annotated[bool, Field(default=False)]
    allowed_client_ips: Annotated[str | None, Field(default=None)]
    redirect: Annotated[str, Field(default="")]
    no_reuse: Annotated[bool, Field(default=False)]

    port: Annotated[int | None, Field(default=None)]
    subdomain: Annotated[str | None, Field(default=None)]


class ProxyRequestModel(AddRequestModel):
    token: str
    session_id: UUID


class AddResponseModel(BaseModel):
    code: int
    url: AnyUrl


class ProxyResponseModel(BaseModel):
    redirect_url: AnyUrl
    reuse: bool


class TokenBodyModel(ConfRequestModel):
    exp: int


@pydantic_api_response_handler
async def check_session_existence(request: web.Request) -> PydanticResponse[StubResponseModel]:
    root_ctx: RootContext = request.app["_root.context"]
    try:
        session_id = UUID(request.match_info["session_id"])
    except ValueError:
        raise ObjectNotFound(object_name="Circuit")

    token = request.match_info["token"]

    for _, circuit in root_ctx.proxy_frontend.circuits.items():
        if session_id in circuit.session_ids and (
            token == circuit.access_key or token == circuit.user_id
        ):
            break
    else:
        raise ObjectNotFound(object_name="Circuit")

    return PydanticResponse(StubResponseModel(success=True))


@pydantic_api_response_handler
async def delete_circuit_by_session(request: web.Request) -> PydanticResponse[StubResponseModel]:
    root_ctx: RootContext = request.app["_root.context"]
    try:
        session_id = UUID(request.match_info["session_id"])
    except ValueError:
        raise ObjectNotFound(object_name="Circuit")

    token = request.match_info["token"]

    for _, circuit in root_ctx.proxy_frontend.circuits.items():
        if session_id in circuit.session_ids and (
            token == circuit.access_key or token == str(circuit.user_id)
        ):
            break
    else:
        raise ObjectNotFound(object_name="Circuit")
    permit_key = request.query.get("permit_key")
    if (
        not permit_key
        or not circuit.user_id
        or (
            not is_permit_valid(
                root_ctx.local_config.wsproxy.permit_hash_key, circuit.user_id, permit_key
            )
        )
    ):
        raise GenericForbidden

    await root_ctx.proxy_frontend.break_circuit(circuit)
    return PydanticResponse(StubResponseModel(success=True))


@pydantic_api_handler(AddRequestModel, is_deprecated=True)
async def add(request: web.Request, params: AddRequestModel) -> PydanticResponse[AddResponseModel]:
    """
    Deprecated: only for legacy applications. Just call `proxy` API directly.
    Returns URL to AppProxy's `proxy` API handler.
    """
    root_ctx: RootContext = request.app["_root.context"]

    config = root_ctx.local_config.wsproxy
    base_url = (
        f"http://{config.advertised_host}:{config.advertised_api_port or config.bind_api_port}"
    )
    qdict = {
        **params.model_dump(mode="json", exclude_defaults=True),
        "token": request.match_info["token"],
        "session_id": request.match_info["session_id"],
    }
    return PydanticResponse(
        AddResponseModel(
            code=200, url=AnyUrl(f"{base_url}/v2/proxy/auth?{urllib.parse.urlencode(qdict)}")
        ),
    )


@pydantic_api_handler(ProxyRequestModel)
async def proxy(
    request: web.Request, params: ProxyRequestModel
) -> PydanticResponse[ProxyResponseModel] | web.HTTPPermanentRedirect:
    """
    Assigns worker to host proxy app and starts proxy process.
    When `Accept` HTTP header is set to `application/json` access information to worker will be handed out inside response body;
    otherwise wsproxy will try to automatically redirect callee via `Location: ` response header.
    """
    log: LoggerAdapter = request["log"]

    existing_circuit: Circuit | None = None
    circuit: Circuit
    reuse = False

    root_ctx: RootContext = request.app["_root.context"]
    token_str = params.token
    session_id = params.session_id

    token = jwt.decode(
        token_str, root_ctx.local_config.wsproxy.jwt_encrypt_key, algorithms=["HS256"]
    )

    if token["session_id"] != str(session_id):
        log.warn(
            "User requested to create app of session {} but token authorizes session {}",
            session_id,
            token["session_id"],
        )
        raise InvalidCredentials

    for _, circuit in root_ctx.proxy_frontend.circuits.items():
        if (
            token["session_id"] in circuit.session_ids
            and token["app"] == circuit.app
            and token.get("open_to_public", False) == circuit.open_to_public
            and token["allowed_client_ip"] == circuit.allowed_client_ips
        ) and not params.no_reuse:
            existing_circuit = circuit
            break

    if existing_circuit:
        reuse = True
        routes = existing_circuit.route_info
        circuit = existing_circuit
    else:
        routes = [
            RouteInfo(
                session_id=token["session_id"],
                session_name=None,
                kernel_host=token["kernel_host"],
                kernel_port=token["kernel_port"],
                protocol=params.protocol,
                traffic_ratio=1.0,
            )
        ]

        log.debug("protocol: {} ({})", params.protocol, type(params.protocol))
        if params.protocol == ProxyProtocol.PREOPEN:
            log.debug("overriding PREOPEN to HTTP")
            params.protocol = ProxyProtocol.HTTP

        circuit = await add_circuit(
            root_ctx,
            SessionConfig(
                id=token["session_id"],
                user_uuid=token["user_uuid"],
                group_id=token["group_id"],
                access_key=token["access_key"],
                domain_name=token["domain_name"],
            ),
            None,
            params.app,
            params.protocol,
            AppMode.INTERACTIVE,
            routes,
            envs=params.envs,
            args=params.args,
            open_to_public=params.open_to_public,
            allowed_client_ips=params.allowed_client_ips,
        )
        log.debug("created new circuit")

    token_to_generate_body = {
        "version": "v2",  # TODO: add support for v1
        "redirect": params.redirect,
        "circuit": str(circuit.id),
    }
    qdict = {
        "token": jwt.encode(token_to_generate_body, root_ctx.local_config.wsproxy.jwt_encrypt_key),
    }

    port = (
        root_ctx.local_config.wsproxy.advertised_api_port
        or root_ctx.local_config.wsproxy.bind_api_port
    )
    app_url = f"http://{root_ctx.local_config.wsproxy.advertised_host}:{port}/setup?{urllib.parse.urlencode(qdict)}"
    log.debug("Redirect URL created: {}", app_url)

    if mime_match(request.headers.get("accept", "text/html"), "application/json", strict=True):
        # Web browsers block redirect between cross-origins if Access-Control-Allow-Origin value is set to a concrete Origin instead of wildcard;
        # Hence we need to send "*" as allowed origin manually, instead of benefiting from aiohttp-cors
        return PydanticResponse(
            ProxyResponseModel(
                redirect_url=AnyUrl(app_url),
                # Current version of WebUI always expects this to be False for TCP protocols
                reuse=reuse if params.protocol != ProxyProtocol.TCP else False,
            ),
        )
    else:
        return web.HTTPPermanentRedirect(app_url)


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v2/proxy"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("GET", "/{token}/{session_id}", check_session_existence))
    cors.add(app.router.add_route("GET", "/{token}/{session_id}/add", add))
    cors.add(app.router.add_route("GET", "/{token}/{session_id}/delete", delete_circuit_by_session))
    cors.add(app.router.add_route("GET", "/auth", proxy))
    return app, []
