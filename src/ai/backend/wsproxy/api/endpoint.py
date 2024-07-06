import textwrap
from datetime import datetime
from typing import Annotated, Iterable
from uuid import UUID

import aiohttp_cors
import jwt
from aiohttp import web
from pydantic import AnyUrl, BaseModel, Field

from ai.backend.wsproxy.exceptions import ObjectNotFound
from ai.backend.wsproxy.types import (
    AppMode,
    CORSOptions,
    EndpointConfig,
    ProxyProtocol,
    PydanticResponse,
    RouteInfo,
    WebMiddleware,
)

from ..defs import RootContext
from ..registry import add_circuit
from ..types import SessionConfig
from .types import StubResponseModel
from .utils import (
    auth_required,
    pydantic_api_handler,
    pydantic_api_response_handler,
)


class EndpointTagConfig(BaseModel):
    session: SessionConfig
    endpoint: EndpointConfig


class InferenceAppConfig(BaseModel):
    session_id: UUID
    kernel_host: str
    kernel_port: int
    protocol: Annotated[ProxyProtocol, Field(default=ProxyProtocol.HTTP)]
    traffic_ratio: Annotated[float, Field(ge=0.0, le=1.0, default=1.0)]


class EndpointCreationRequestModel(BaseModel):
    service_name: Annotated[str, Field(description="Name of the model service.")]
    tags: Annotated[
        EndpointTagConfig,
        Field(
            description="Metadata of target model service and dependent sessions.",
        ),
    ]
    apps: Annotated[
        dict[str, list[InferenceAppConfig]],
        Field(
            description=textwrap.dedent(
                """
                key-value pair of available applications exposed by requested endpoint.
                Key should be name of the app, and value as list of host-port pairs app is bound to.
                """
            ),
        ),
    ]
    open_to_public: Annotated[
        bool,
        Field(
            default=False,
            description=textwrap.dedent(
                """
                If set to true, AppProxy will require an API token (which can be obtained from `generate_endpoint_api_token` request)
                fullfilled at request header.
                """
            ),
        ),
    ]

    port: Annotated[int | None, Field(default=None, description="Preferred port number.")]
    subdomain: Annotated[str | None, Field(default=None, description="Preferred subdomain name.")]


class EndpointCreationResponseModel(BaseModel):
    endpoint: AnyUrl


@auth_required("manager")
@pydantic_api_handler(EndpointCreationRequestModel)
async def create_or_update_endpoint(
    request: web.Request, params: EndpointCreationRequestModel
) -> PydanticResponse[EndpointCreationResponseModel]:
    """
    Creates or updates an inference circuit.
    """
    root_ctx: RootContext = request.app["_root.context"]
    endpoint_id = UUID(request.match_info["endpoint_id"])

    app_names = list(params.apps.keys())
    if len(app_names) > 0:
        app = list(params.apps.keys())[0]
        routes = [RouteInfo(**r.model_dump()) for r in params.apps[app]]
    else:
        app = ""
        routes = []

    try:
        circuit = root_ctx.proxy_frontend.get_circuit_by_endpoint_id(endpoint_id)
        circuit.route_info = routes
        circuit.session_ids = [r.session_id for r in routes]
        circuit.open_to_public = params.open_to_public
        await root_ctx.proxy_frontend.update_circuit_route_info(circuit, routes)
    except ObjectNotFound:
        circuit = await add_circuit(
            root_ctx,
            params.tags.session,
            params.tags.endpoint,
            app,
            params.apps[app][0].protocol if app else ProxyProtocol.HTTP,
            AppMode.INFERENCE,
            routes,
            open_to_public=params.open_to_public,
        )
    endpoint_url = f"http://{root_ctx.local_config.wsproxy.advertised_host}:{circuit.port}"

    return PydanticResponse(EndpointCreationResponseModel(endpoint=AnyUrl(endpoint_url)))


@auth_required("manager")
@pydantic_api_response_handler
async def remove_endpoint(request: web.Request) -> PydanticResponse[StubResponseModel]:
    """
    Deassociates inference circuit from system.
    """
    root_ctx: RootContext = request.app["_root.context"]

    endpoint_id = UUID(request.match_info["endpoint_id"])

    circuit = root_ctx.proxy_frontend.get_circuit_by_endpoint_id(endpoint_id)
    await root_ctx.proxy_frontend.break_circuit(circuit)

    return PydanticResponse(StubResponseModel(success=True))


class EndpointAPITokenGenerationRequestModel(BaseModel):
    user_uuid: UUID
    """
    Token requester's user UUID.
    """
    exp: datetime
    """
    Expiration date of token.
    """


class EndpointAPITokenResponseModel(BaseModel):
    token: str


@auth_required("manager")
@pydantic_api_handler(EndpointAPITokenGenerationRequestModel)
async def generate_endpoint_api_token(
    request: web.Request, params: EndpointAPITokenGenerationRequestModel
) -> PydanticResponse[EndpointAPITokenResponseModel]:
    """
    Creates and returns API token required for execution of model service apps hosted by AppProxy.
     This API is meant to be called from Backend.AI manager rather than model service callee itself.
    """
    root_ctx: RootContext = request.app["_root.context"]

    endpoint_id = UUID(request.match_info["endpoint_id"])

    circuit = root_ctx.proxy_frontend.get_circuit_by_endpoint_id(endpoint_id)
    await root_ctx.proxy_frontend.break_circuit(circuit)
    payload = circuit.model_dump(mode="json")
    payload["config"] = {}
    payload["app_url"] = f"http://{root_ctx.local_config.wsproxy.advertised_host}:{circuit.port}"
    payload["user"] = str(params.user_uuid)
    payload["exp"] = params.exp
    encoded_jwt = jwt.encode(
        payload, root_ctx.local_config.wsproxy.jwt_encrypt_key, algorithm="HS256"
    )
    return PydanticResponse(EndpointAPITokenResponseModel(token=encoded_jwt))


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v2/endpoints"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(app.router.add_resource(r""))
    cors.add(add_route("POST", "/{endpoint_id}", create_or_update_endpoint))
    cors.add(add_route("DELETE", "/{endpoint_id}", remove_endpoint))
    cors.add(add_route("POST", "/{endpoint_id}/token", generate_endpoint_api_token))
    return app, []
