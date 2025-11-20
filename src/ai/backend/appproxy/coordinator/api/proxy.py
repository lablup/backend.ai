from __future__ import annotations

import logging
import urllib.parse
from typing import TYPE_CHECKING, Annotated, Iterable, Optional
from uuid import UUID

import jwt
from aiohttp import web
from pydantic import AnyUrl, BaseModel, Field

from ai.backend.appproxy.common.exceptions import (
    InvalidCredentials,
    ObjectNotFound,
)
from ai.backend.appproxy.common.types import (
    AppMode,
    CORSOptions,
    ProxyProtocol,
    PydanticResponse,
    RouteInfo,
    SessionConfig,
    WebMiddleware,
)
from ai.backend.appproxy.common.utils import mime_match, pydantic_api_handler
from ai.backend.appproxy.coordinator.api.types import ConfRequestModel
from ai.backend.logging import BraceStyleAdapter

from ..models import Circuit, Token, Worker, add_circuit
from ..models.utils import execute_with_txn_retry
from ..types import RootContext

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


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


@pydantic_api_handler(AddRequestModel, is_deprecated=True)
async def add(request: web.Request, params: AddRequestModel) -> PydanticResponse[AddResponseModel]:
    """
    Deprecated: only for legacy applications. Just call `proxy` API directly.
    Returns URL to AppProxy's `proxy` API handler.
    """
    root_ctx: RootContext = request.app["_root.context"]

    coordinator_config = root_ctx.local_config.proxy_coordinator
    base_url = coordinator_config.advertise_base_url
    qdict = {
        **params.model_dump(mode="json", exclude_defaults=True),
        "token": request.match_info["token"],
        "session_id": request.match_info["session_id"],
    }
    return PydanticResponse(
        AddResponseModel(
            code=200, url=AnyUrl(f"{base_url}/v2/proxy/auth?{urllib.parse.urlencode(qdict)}")
        ),
        headers={"Access-Control-Allow-Origin": "*", "Access-Control-Expose-Headers": "*"},
    )


@pydantic_api_handler(ProxyRequestModel)
async def proxy(
    request: web.Request, params: ProxyRequestModel
) -> PydanticResponse[ProxyResponseModel] | web.HTTPPermanentRedirect:
    """
    Assigns worker to host proxy app and starts proxy process.
    When `Accept` HTTP header is set to `application/json` access information to worker will be handed out inside response body;
    otherwise coordinator will try to automatically redirect callee via `Location: ` response header.
    """

    existing_circuit: Optional[Circuit] = None
    reuse = False

    root_ctx: RootContext = request.app["_root.context"]
    token_id = params.token
    session_id = params.session_id

    async with root_ctx.db.begin_readonly_session() as sess:
        token = await Token.get(sess, UUID(token_id))

    if token.session_id != session_id:
        log.warning(
            "User requested to create app of session {} but token authorizes session {}",
            session_id,
            token.session_id,
        )
        raise InvalidCredentials("E20007: Session ID mismatch")

    if not params.no_reuse:
        async with root_ctx.db.begin_readonly_session() as sess:
            try:
                existing_circuit = await Circuit.find(
                    sess,
                    token.session_id,
                    params.app,
                    params.open_to_public,
                    params.allowed_client_ips,
                )
            except ObjectNotFound:
                existing_circuit = None

    if existing_circuit:
        reuse = True
        routes = existing_circuit.route_info
        async with root_ctx.db.begin_readonly_session() as sess:
            worker = await Worker.get(sess, existing_circuit.worker)
        log.debug("reusing existing circuit {}", existing_circuit.id)
        circuit = existing_circuit
    else:
        routes = [
            RouteInfo(
                session_id=token.session_id,
                session_name=None,
                kernel_host=token.kernel_host,
                kernel_port=token.kernel_port,
                protocol=params.protocol,
                traffic_ratio=1.0,
                route_id=None,
                health_status=None,
                last_health_check=None,
                consecutive_failures=0,
            )
        ]

        log.debug("protocol: {} ({})", params.protocol, type(params.protocol))
        if params.protocol == ProxyProtocol.PREOPEN:
            log.debug("overriding PREOPEN to HTTP")
            params.protocol = ProxyProtocol.HTTP

        async def _update(sess: SASession) -> tuple[Circuit, Worker]:
            circuit, worker = await add_circuit(
                sess,
                SessionConfig(
                    id=token.session_id,
                    user_uuid=token.user_uuid,
                    group_id=token.group_id,
                    access_key=token.access_key,
                    domain_name=token.domain_name,
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
                preferred_port=params.port,
                preferred_subdomain=params.subdomain,
            )
            return circuit, worker

        async with root_ctx.db.connect() as db_conn:
            circuit, worker = await execute_with_txn_retry(
                _update, root_ctx.db.begin_session, db_conn
            )
        log.debug("created new circuit {}", circuit.id)

    assert circuit and worker

    await root_ctx.circuit_manager.initialize_circuits([circuit])

    assert circuit
    log.debug("Circuit is set (id:{})", str(circuit.id))
    token_to_generate_body = {
        "id": str(token.id),
        "version": "v2",  # TODO: add support for v1
        "redirect": params.redirect,
        "circuit": str(circuit.id),
    }
    qdict = {
        "token": jwt.encode(token_to_generate_body, root_ctx.local_config.secrets.jwt_secret),
    }

    app_url = f"{worker.api_endpoint}/setup?{urllib.parse.urlencode(qdict)}"
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
            headers={"Access-Control-Allow-Origin": "*", "Access-Control-Expose-Headers": "*"},
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
    app.router.add_route("GET", "/{token}/{session_id}/add", add)
    app.router.add_route("GET", "/auth", proxy)
    return app, []
