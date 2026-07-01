from __future__ import annotations

import textwrap
from collections.abc import Iterable
from datetime import datetime
from typing import Annotated
from uuid import UUID

import aiohttp_cors
from aiohttp import web
from pydantic import AnyUrl, Field

from ai.backend.appproxy.common.errors import ObjectNotFound
from ai.backend.appproxy.common.types import (
    AppMode,
    CORSOptions,
    EndpointConfig,
    PydanticResponse,
    SessionConfig,
    WebMiddleware,
)
from ai.backend.appproxy.common.utils import (
    pydantic_api_handler,
    pydantic_api_response_handler,
)
from ai.backend.appproxy.coordinator.errors import InvalidCircuitStateError
from ai.backend.appproxy.coordinator.models import Circuit
from ai.backend.appproxy.coordinator.types import RootContext
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.request import (
    BulkCreateEndpointRequest,
    BulkDeleteEndpointRequest,
    BulkRegisterRoutesRequest,
    BulkUnregisterRoutesRequest,
    BulkUpdateRoutesRequest,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.response import (
    BulkCreateEndpointResponse,
    BulkDeleteEndpointResponse,
    BulkRegisterRoutesResponse,
    BulkUnregisterRoutesResponse,
    BulkUpdateRoutesResponse,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    CreateEndpointItem,
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.types import BackendAISchema

from .types import StubResponseModel
from .utils import auth_required


class EndpointTagConfig(BackendAISchema):
    session: SessionConfig
    endpoint: EndpointConfig


class EndpointCreationRequestModel(BackendAISchema):
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
        ModelHealthCheck | None,
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


class EndpointCreationResponseModel(BackendAISchema):
    success: bool
    endpoint: AnyUrl
    health_check_enabled: bool


def _request_model_to_item(
    deployment_id: DeploymentID, params: EndpointCreationRequestModel
) -> CreateEndpointItem:
    """Adapt the single-endpoint coordinator DTO to the common-DTO item."""
    return CreateEndpointItem(
        deployment_id=deployment_id,
        version=params.version,
        service_name=params.service_name,
        tags=TagsModel(
            session=SessionTagsModel.model_validate(params.tags.session.model_dump()),
            endpoint=EndpointTagsModel.model_validate(params.tags.endpoint.model_dump()),
        ),
        open_to_public=params.open_to_public,
        health_check=params.health_check,
    )


@auth_required("manager")
@pydantic_api_handler(EndpointCreationRequestModel)
async def create_or_update_endpoint(
    request: web.Request, params: EndpointCreationRequestModel
) -> PydanticResponse[EndpointCreationResponseModel]:
    """Create or sync a single inference endpoint + circuit."""
    root_ctx: RootContext = request.app["_root.context"]
    deployment_id = DeploymentID(UUID(request.match_info["endpoint_id"]))

    result = await root_ctx.endpoint_service.sync_endpoint(
        _request_model_to_item(deployment_id, params)
    )
    return PydanticResponse(
        EndpointCreationResponseModel(
            success=True,
            endpoint=result.url,
            health_check_enabled=result.health_check_enabled,
        )
    )


@auth_required("manager")
@pydantic_api_handler(BulkCreateEndpointRequest)
async def bulk_create_or_update_endpoints(
    request: web.Request, params: BulkCreateEndpointRequest
) -> PydanticResponse[BulkCreateEndpointResponse]:
    """Bulk create / sync many inference endpoints in one coordinator call."""
    root_ctx: RootContext = request.app["_root.context"]
    items = await root_ctx.endpoint_service.sync_endpoints_bulk(params.endpoints)
    return PydanticResponse(BulkCreateEndpointResponse(endpoints=items))


@auth_required("manager")
@pydantic_api_response_handler
async def remove_endpoint(request: web.Request) -> PydanticResponse[StubResponseModel]:
    """Deassociate a single inference endpoint + circuit from the proxy."""
    root_ctx: RootContext = request.app["_root.context"]
    deployment_id = DeploymentID(UUID(request.match_info["endpoint_id"]))
    await root_ctx.endpoint_service.delete_endpoint(deployment_id)
    return PydanticResponse(StubResponseModel(success=True))


@auth_required("manager")
@pydantic_api_handler(BulkDeleteEndpointRequest)
async def bulk_remove_endpoints(
    request: web.Request, params: BulkDeleteEndpointRequest
) -> PydanticResponse[BulkDeleteEndpointResponse]:
    """Bulk delete inference endpoints in one coordinator call."""
    root_ctx: RootContext = request.app["_root.context"]
    deployment_ids = [item.deployment_id for item in params.endpoints]
    items = await root_ctx.endpoint_service.delete_endpoints_bulk(deployment_ids)
    return PydanticResponse(BulkDeleteEndpointResponse(endpoints=items))


@auth_required("manager")
@pydantic_api_handler(BulkUpdateRoutesRequest)
async def bulk_update_routes(
    request: web.Request, params: BulkUpdateRoutesRequest
) -> PydanticResponse[BulkUpdateRoutesResponse]:
    """Bulk replace routing tables for many endpoints in one coordinator call."""
    root_ctx: RootContext = request.app["_root.context"]
    items = await root_ctx.endpoint_service.update_routes_bulk(params.endpoints)
    return PydanticResponse(BulkUpdateRoutesResponse(endpoints=items))


@auth_required("manager")
@pydantic_api_handler(BulkRegisterRoutesRequest)
async def bulk_register_routes(
    request: web.Request, params: BulkRegisterRoutesRequest
) -> PydanticResponse[BulkRegisterRoutesResponse]:
    """Bulk add new routes to many endpoints (delta semantics)."""
    root_ctx: RootContext = request.app["_root.context"]
    items = await root_ctx.endpoint_service.register_routes_bulk(params.endpoints)
    return PydanticResponse(BulkRegisterRoutesResponse(endpoints=items))


@auth_required("manager")
@pydantic_api_handler(BulkUnregisterRoutesRequest)
async def bulk_unregister_routes(
    request: web.Request, params: BulkUnregisterRoutesRequest
) -> PydanticResponse[BulkUnregisterRoutesResponse]:
    """Bulk drop routes from many endpoints (delta semantics)."""
    root_ctx: RootContext = request.app["_root.context"]
    items = await root_ctx.endpoint_service.unregister_routes_bulk(params.endpoints)
    return PydanticResponse(BulkUnregisterRoutesResponse(endpoints=items))


class UpdateModelHealthCheckRequestModel(BackendAISchema):
    health_check: ModelHealthCheck | None


@auth_required("manager")
@pydantic_api_handler(UpdateModelHealthCheckRequestModel)
async def inject_health_check_information(
    request: web.Request, params: UpdateModelHealthCheckRequestModel
) -> PydanticResponse[StubResponseModel]:
    """Update the health-check configuration of an existing endpoint in-place."""
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_session() as sess:
        circuit: Circuit = await Circuit.find_by_endpoint(
            sess, UUID(request.match_info["endpoint_id"]), load_worker=False
        )
        if circuit.app_mode != AppMode.INFERENCE:
            raise ObjectNotFound(object_name="inference-circuit")

        if not circuit.endpoint_row:
            raise InvalidCircuitStateError("Endpoint row is not loaded for circuit")
        circuit.endpoint_row.health_check_enabled = params.health_check is not None
        circuit.endpoint_row.health_check_config = params.health_check

    return PydanticResponse(StubResponseModel(success=True))


class EndpointAPITokenGenerationRequestModel(BackendAISchema):
    user_uuid: UUID
    """
    Token requester's user UUID.
    """
    exp: datetime
    """
    Expiration date of token.
    """


class EndpointAPITokenResponseModel(BackendAISchema):
    token: str


@auth_required("manager")
@pydantic_api_handler(EndpointAPITokenGenerationRequestModel)
async def generate_endpoint_api_token(
    request: web.Request, params: EndpointAPITokenGenerationRequestModel
) -> PydanticResponse[EndpointAPITokenResponseModel]:
    """Issue an API token that proxied model-service apps can authenticate with."""
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        circuit = await Circuit.find_by_endpoint(
            sess, UUID(request.match_info["endpoint_id"]), load_worker=False, load_endpoint=False
        )
        encoded_jwt = await circuit.generate_jwt(
            sess, root_ctx.local_config.secrets.jwt_secret, params.user_uuid, params.exp
        )
    return PydanticResponse(EndpointAPITokenResponseModel(token=encoded_jwt))


async def init(_app: web.Application) -> None:
    pass


async def shutdown(_app: web.Application) -> None:
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
    # Static '/bulk' routes must be registered before the parametric
    # '/{endpoint_id}' so aiohttp doesn't resolve them to the parametric handler.
    cors.add(add_route("POST", "/bulk/routes/register", bulk_register_routes))
    cors.add(add_route("POST", "/bulk/routes/unregister", bulk_unregister_routes))
    cors.add(add_route("POST", "/bulk/routes", bulk_update_routes))
    cors.add(add_route("POST", "/bulk", bulk_create_or_update_endpoints))
    cors.add(add_route("DELETE", "/bulk", bulk_remove_endpoints))
    cors.add(add_route("POST", "/{endpoint_id}", create_or_update_endpoint))
    cors.add(add_route("PUT", "/{endpoint_id}/health-check", inject_health_check_information))
    cors.add(add_route("DELETE", "/{endpoint_id}", remove_endpoint))
    cors.add(add_route("POST", "/{endpoint_id}/token", generate_endpoint_api_token))
    return app, []
