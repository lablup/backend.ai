from __future__ import annotations

import textwrap
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Iterable
from uuid import UUID

import aiohttp_cors
import jwt
import sqlalchemy as sa
from aiohttp import web
from pydantic import AnyUrl, BaseModel, Field
from yarl import URL

from ai.backend.appproxy.common.exceptions import ObjectNotFound
from ai.backend.appproxy.common.types import (
    AppMode,
    CORSOptions,
    EndpointConfig,
    FrontendMode,
    HealthCheckConfig,
    ProxyProtocol,
    PydanticResponse,
    WebMiddleware,
)
from ai.backend.appproxy.common.utils import (
    pydantic_api_handler,
    pydantic_api_response_handler,
)
from ai.backend.appproxy.coordinator.models.worker import add_circuit

from ..models import Circuit, Endpoint, Worker
from ..models.utils import execute_with_txn_retry
from ..types import RootContext
from .types import SessionConfig, StubResponseModel
from .utils import auth_required

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


class EndpointTagConfig(BaseModel):
    session: SessionConfig
    endpoint: EndpointConfig


class EndpointCreationRequestModel(BaseModel):
    version: Annotated[str, Field(description="Creation API version")]
    service_name: Annotated[str, Field(description="Name of the model service.")]
    tags: Annotated[
        EndpointTagConfig,
        Field(
            description="Metadata of target model service and dependent sessions.",
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
    ] = False

    port: Annotated[int | None, Field(default=None, description="Preferred port number.")] = None
    subdomain: Annotated[
        str | None, Field(default=None, description="Preferred subdomain name.")
    ] = None

    health_check: Annotated[
        HealthCheckConfig | None,
        Field(
            default=None,
            description=textwrap.dedent(
                """
                Health check configuration for the model service.
                If provided, enables health checking for this endpoint.
                Matches model-definition.yaml health check schema.
                Only used when version is 'v2'.
                """
            ),
        ),
    ] = None


class EndpointCreationResponseModel(BaseModel):
    success: bool
    endpoint: AnyUrl
    health_check_enabled: bool


@auth_required("manager")
@pydantic_api_handler(EndpointCreationRequestModel)
async def create_or_update_endpoint(
    request: web.Request, params: EndpointCreationRequestModel
) -> PydanticResponse[EndpointCreationResponseModel]:
    """
    Creates or updates an inference circuit (v1) or syncs endpoint health check configuration (v2).
    Version is determined by the 'version' field in the request body.
    """
    root_ctx: RootContext = request.app["_root.context"]
    endpoint_id = UUID(request.match_info["endpoint_id"])

    health_check_config = params.health_check
    health_check_enabled = health_check_config is not None

    async def _sync(sess: SASession) -> URL:
        # Check if endpoint already exists
        try:
            endpoint = await Endpoint.get(sess, endpoint_id, load_circuit=False)
            # Update health check configuration
            endpoint.health_check_enabled = health_check_enabled
            endpoint.health_check_config = health_check_config
        except ObjectNotFound:
            # Create new endpoint record
            endpoint = Endpoint.create(
                endpoint_id=endpoint_id,
                health_check_enabled=health_check_enabled,
                health_check_config=health_check_config,
            )
            sess.add(endpoint)

        # Check if circuit already exists for this endpoint
        try:
            circuit = await Circuit.get_by_endpoint(
                sess, endpoint_id, load_worker=True, load_endpoint=True
            )
            circuit.endpoint_row = endpoint
            # Return existing circuit URL
            return await circuit.get_endpoint_url()
        except ObjectNotFound:
            pass  # Continue with creating new circuit

        # supported for subdomain based workers only
        matched_worker_id: UUID | None = None
        if _url := params.tags.endpoint.existing_url:
            assert _url.host
            domain = "." + ".".join(_url.host.split(".")[1:])

            query = sa.select(Worker).where(
                (
                    Worker.accepted_traffics.contains([AppMode.INFERENCE])
                    & (Worker.frontend_mode == FrontendMode.WILDCARD_DOMAIN)
                    & (Worker.wildcard_domain == domain)
                )
            )
            result = await sess.execute(query)
            matched_worker = result.scalar()
            if matched_worker:
                params.subdomain = _url.host.split(".")[0]
            else:
                assert _url.port
                query = sa.select(Worker).where(
                    (
                        Worker.accepted_traffics.contains([AppMode.INFERENCE])
                        & (Worker.frontend_mode == FrontendMode.PORT)
                        & (Worker.hostname == _url.host)
                    )
                )
                result = await sess.execute(query)
                worker_candidates = result.scalars().all()
                matched_workers = [
                    w
                    for w in worker_candidates
                    if w.port_range and w.port_range[0] <= _url.port <= w.port_range[1]
                ]
                if matched_workers:
                    params.port = _url.port
                    matched_worker = matched_workers[0]
                else:
                    matched_worker = None
            if matched_worker:
                matched_worker_id = matched_worker.id
        circuit, worker = await add_circuit(
            sess,
            params.tags.session,
            params.tags.endpoint,
            params.service_name,
            ProxyProtocol.HTTP,
            AppMode.INFERENCE,
            [],
            open_to_public=params.open_to_public,
            preferred_port=params.port,
            preferred_subdomain=params.subdomain or params.service_name,
            worker_id=matched_worker_id,
        )
        circuit.endpoint_id = endpoint.id
        circuit.endpoint_row = endpoint
        await root_ctx.circuit_manager.initialize_circuits([circuit])

        # Circuit already references endpoint by endpoint_id, no need to update
        # The relationship is handled automatically through endpoint_id matching

        # Route health status is now managed directly in the JSON route_info
        # Health status will be populated by the health checker when enabled

        await sess.flush()
        return await circuit.get_endpoint_url()

    async with root_ctx.db.connect() as db_conn:
        endpoint_url = await execute_with_txn_retry(_sync, root_ctx.db.begin_session, db_conn)

    return PydanticResponse(
        EndpointCreationResponseModel(
            success=True,
            endpoint=AnyUrl(str(endpoint_url)),
            health_check_enabled=health_check_enabled,
        )
    )


@auth_required("manager")
@pydantic_api_response_handler
async def remove_endpoint(request: web.Request) -> PydanticResponse[StubResponseModel]:
    """
    Deassociates inference circuit from system.
    """
    root_ctx: RootContext = request.app["_root.context"]

    endpoint_id = UUID(request.match_info["endpoint_id"])

    async def _update(sess: SASession) -> None:
        endpoint = await Endpoint.get(sess, endpoint_id, load_circuit=True)
        circuit = await Circuit.get(sess, endpoint.circuit_row.id, load_worker=True)
        circuit.worker_row.occupied_slots -= 1
        await sess.delete(circuit)
        await sess.delete(endpoint)

        await root_ctx.circuit_manager.unload_circuits([circuit])

    async with root_ctx.db.connect() as db_conn:
        await execute_with_txn_retry(_update, root_ctx.db.begin_session, db_conn)
    return PydanticResponse(StubResponseModel(success=True))


class UpdateHealthCheckConfigRequestModel(BaseModel):
    health_check: HealthCheckConfig | None


@auth_required("manager")
@pydantic_api_handler(UpdateHealthCheckConfigRequestModel)
async def inject_health_check_information(
    request: web.Request, params: UpdateHealthCheckConfigRequestModel
) -> PydanticResponse[StubResponseModel]:
    """
    Creates and returns API token required for execution of model service apps hosted by AppProxy.
     This API is meant to be called from Backend.AI manager rather than model service callee itself.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_session() as sess:
        circuit: Circuit = await Circuit.find_by_endpoint(
            sess, UUID(request.match_info["endpoint_id"]), load_worker=False
        )
        if circuit.app_mode != AppMode.INFERENCE:
            raise ObjectNotFound(object_name="inference-circuit")

        assert circuit.endpoint_row
        circuit.endpoint_row.health_check_enabled = params.health_check is not None
        circuit.endpoint_row.health_check_config = params.health_check

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

    async with root_ctx.db.begin_readonly_session() as sess:
        circuit: Circuit = await Circuit.find_by_endpoint(
            sess, UUID(request.match_info["endpoint_id"]), load_worker=False, load_endpoint=False
        )
        payload = dict(circuit.dump_model())
        payload["config"] = {}
        payload["app_url"] = str(await circuit.get_endpoint_url(session=sess))

    payload["user"] = str(params.user_uuid)
    payload["exp"] = params.exp
    encoded_jwt = jwt.encode(payload, root_ctx.local_config.secrets.jwt_secret, algorithm="HS256")
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
    cors.add(add_route("PUT", "/{endpoint_id}/health-check", inject_health_check_information))
    cors.add(add_route("DELETE", "/{endpoint_id}", remove_endpoint))
    cors.add(add_route("POST", "/{endpoint_id}/token", generate_endpoint_api_token))
    return app, []
