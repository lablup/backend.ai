"""Health monitoring API endpoints"""

import logging
from datetime import datetime
from typing import Iterable, Literal
from uuid import UUID

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import BaseModel

from ai.backend.appproxy.common.types import AppMode, CORSOptions, PydanticResponse, WebMiddleware
from ai.backend.appproxy.common.utils import pydantic_api_response_handler
from ai.backend.common.types import ModelServiceStatus
from ai.backend.logging import BraceStyleAdapter

from .. import __version__
from ..models import Circuit, Endpoint, Worker
from ..types import RootContext
from .utils import auth_required

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class RouteHealthStatusModel(BaseModel):
    """Model for individual route health status"""

    route_id: UUID
    session_id: UUID
    kernel_host: str
    kernel_port: int
    protocol: str
    health_status: ModelServiceStatus | None
    last_health_check: float | None
    consecutive_failures: int
    created_at: datetime
    updated_at: datetime


class EndpointHealthStatusModel(BaseModel):
    """Model for endpoint health status summary"""

    endpoint_id: UUID
    health_check_enabled: bool
    total_routes: int
    healthy_routes: int
    unhealthy_routes: int
    unknown_routes: int
    routes: list[RouteHealthStatusModel]


class CircuitHealthStatusModel(BaseModel):
    """Model for circuit health status with route details"""

    circuit_id: UUID
    endpoint_id: UUID | None
    total_routes: int
    healthy_routes: int
    all_routes: list[RouteHealthStatusModel]


class HealthSummaryModel(BaseModel):
    """Model for overall health summary"""

    total_endpoints: int
    endpoints_with_health_checks: int
    total_routes: int
    healthy_routes: int
    unhealthy_routes: int
    unknown_routes: int


class HealthStatusResponseModel(BaseModel):
    """Response model for health status APIs"""

    success: bool
    summary: HealthSummaryModel | None = None
    endpoints: list[EndpointHealthStatusModel] | None = None
    circuits: list[CircuitHealthStatusModel] | None = None


class WorkerInfoModel(BaseModel):
    authority: str
    available_slots: int
    occupied_slots: int
    ha_setup: bool


class StatusResponseModel(BaseModel):
    coordinator_version: str
    appproxy_api_version: Literal["v2"]
    workers: list[WorkerInfoModel]
    """
    List of active workers (pool of workers which are able to handle proxying job).
    """


@auth_required("manager")
@pydantic_api_response_handler
async def get_health_summary(request: web.Request) -> PydanticResponse[HealthStatusResponseModel]:
    """Get overall health status summary"""
    root_ctx: RootContext = request.app["ctx"]

    async with root_ctx.db.begin_readonly_session() as sess:
        # Get endpoint counts
        endpoints_query = sa.select(sa.func.count(Endpoint.id))
        total_endpoints = await sess.scalar(endpoints_query) or 0

        health_enabled_query = sa.select(sa.func.count(Endpoint.id)).where(
            Endpoint.health_check_enabled.is_(True)
        )
        endpoints_with_health = await sess.scalar(health_enabled_query) or 0

        # Get route health counts by examining circuit route_info JSON
        total_routes = 0
        healthy_routes = 0
        unhealthy_routes = 0
        unknown_routes = 0

        # Query all circuits that have endpoints with health checking enabled and are in INFERENCE mode
        circuit_query = (
            sa.select(Circuit)
            .join(Endpoint, Circuit.endpoint_id == Endpoint.id)
            .where(
                sa.and_(
                    Endpoint.health_check_enabled.is_(True), Circuit.app_mode == AppMode.INFERENCE
                )
            )
        )
        circuits = await sess.execute(circuit_query)

        for circuit in circuits.scalars():
            for route in circuit.route_info:
                if route.route_id:  # Only count routes with IDs (health-checkable)
                    total_routes += 1
                    if route.health_status == ModelServiceStatus.HEALTHY:
                        healthy_routes += 1
                    elif route.health_status == ModelServiceStatus.UNHEALTHY:
                        unhealthy_routes += 1
                    else:
                        unknown_routes += 1

        summary = HealthSummaryModel(
            total_endpoints=total_endpoints,
            endpoints_with_health_checks=endpoints_with_health,
            total_routes=total_routes,
            healthy_routes=healthy_routes,
            unhealthy_routes=unhealthy_routes,
            unknown_routes=unknown_routes,
        )

    return PydanticResponse(HealthStatusResponseModel(success=True, summary=summary))


@auth_required("manager")
@pydantic_api_response_handler
async def get_endpoints_health(request: web.Request) -> PydanticResponse[HealthStatusResponseModel]:
    """Get health status for all endpoints"""
    root_ctx: RootContext = request.app["ctx"]

    async with root_ctx.db.begin_readonly_session() as sess:
        # Get all endpoints with health checking enabled
        endpoints = await Endpoint.list_health_check_enabled(sess)

        endpoint_statuses = []
        for endpoint in endpoints:
            # Find the circuit for this endpoint
            try:
                circuit = await Circuit.find_by_endpoint(sess, endpoint.id)

                # Count health statuses from circuit route_info
                healthy_count = 0
                unhealthy_count = 0
                unknown_count = 0
                route_models = []

                for route in circuit.route_info:
                    if route.route_id:  # Only include routes with IDs (health-checkable)
                        if route.health_status == ModelServiceStatus.HEALTHY:
                            healthy_count += 1
                        elif route.health_status == ModelServiceStatus.UNHEALTHY:
                            unhealthy_count += 1
                        else:
                            unknown_count += 1

                        route_models.append(
                            RouteHealthStatusModel(
                                route_id=route.route_id,
                                session_id=route.session_id,
                                kernel_host=route.kernel_host,
                                kernel_port=route.kernel_port,
                                protocol=route.protocol.value,
                                health_status=route.health_status,
                                last_health_check=route.last_health_check,
                                consecutive_failures=route.consecutive_failures,
                                created_at=circuit.created_at,
                                updated_at=circuit.updated_at,
                            )
                        )

                endpoint_status = EndpointHealthStatusModel(
                    endpoint_id=endpoint.id,
                    health_check_enabled=endpoint.health_check_enabled,
                    total_routes=len(route_models),
                    healthy_routes=healthy_count,
                    unhealthy_routes=unhealthy_count,
                    unknown_routes=unknown_count,
                    routes=route_models,
                )
                endpoint_statuses.append(endpoint_status)

            except Exception as e:
                log.error("Failed to find circuit for endpoint {}: {}", endpoint.id, e)
                # Create empty status for endpoints without circuits
                endpoint_status = EndpointHealthStatusModel(
                    endpoint_id=endpoint.id,
                    health_check_enabled=endpoint.health_check_enabled,
                    total_routes=0,
                    healthy_routes=0,
                    unhealthy_routes=0,
                    unknown_routes=0,
                    routes=[],
                )
                endpoint_statuses.append(endpoint_status)

    return PydanticResponse(HealthStatusResponseModel(success=True, endpoints=endpoint_statuses))


@auth_required("manager")
@pydantic_api_response_handler
async def get_circuit_health(
    request: web.Request,
) -> PydanticResponse[HealthStatusResponseModel]:
    """Get health status for a specific circuit"""
    circuit_id_str = request.match_info["circuit_id"]
    try:
        circuit_id = UUID(circuit_id_str)
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid circuit ID format")

    root_ctx: RootContext = request.app["ctx"]

    async with root_ctx.db.begin_readonly_session() as sess:
        try:
            circuit = await Circuit.get(sess, circuit_id)
        except Exception:
            raise web.HTTPNotFound(reason="Circuit not found")

        if not circuit.endpoint_id:
            # Circuit without endpoint health checking
            circuit_status = CircuitHealthStatusModel(
                circuit_id=circuit.id,
                endpoint_id=None,
                total_routes=len(circuit.route_info),
                healthy_routes=len(circuit.route_info),  # Assume all healthy if no health checking
                all_routes=[],
            )
        else:
            # Get route health from circuit's route_info JSON
            healthy_count = 0
            route_models = []

            for route in circuit.route_info:
                if route.route_id:  # Only include routes with IDs (health-checkable)
                    if route.health_status == ModelServiceStatus.HEALTHY:
                        healthy_count += 1

                    route_models.append(
                        RouteHealthStatusModel(
                            route_id=route.route_id,
                            session_id=route.session_id,
                            kernel_host=route.kernel_host,
                            kernel_port=route.kernel_port,
                            protocol=route.protocol.value,
                            health_status=route.health_status,
                            last_health_check=route.last_health_check,
                            consecutive_failures=route.consecutive_failures,
                            created_at=circuit.created_at,
                            updated_at=circuit.updated_at,
                        )
                    )

            circuit_status = CircuitHealthStatusModel(
                circuit_id=circuit.id,
                endpoint_id=circuit.endpoint_id,
                total_routes=len(route_models),
                healthy_routes=healthy_count,
                all_routes=route_models,
            )

    return PydanticResponse(HealthStatusResponseModel(success=True, circuits=[circuit_status]))


async def hello(request: web.Request) -> web.Response:
    """Simple health check endpoint"""
    from ai.backend.appproxy.common.types import HealthResponse

    request["do_not_print_access_log"] = True

    response = HealthResponse(
        status="healthy",
        version=__version__,
        component="appproxy-coordinator",
    )
    return web.json_response(response.model_dump())


@auth_required("manager")
@pydantic_api_response_handler
async def status(request: web.Request) -> PydanticResponse[StatusResponseModel]:
    """
    Returns health status of coordinator.
    """
    request["do_not_print_access_log"] = True

    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin_readonly_session() as sess:
        workers = await Worker.list_workers(sess)
    return PydanticResponse(
        StatusResponseModel(
            coordinator_version=__version__,
            appproxy_api_version="v2",
            workers=[
                WorkerInfoModel(
                    authority=w.authority,
                    available_slots=w.available_slots,
                    occupied_slots=w.occupied_slots,
                    ha_setup=w.nodes > 1,
                )
                for w in workers
                if (w.updated_at.timestamp() - datetime.now().timestamp()) <= 30
            ],
        )
    )


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "health"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", hello))
    cors.add(add_route("GET", "/status", status))
    cors.add(add_route("GET", "/summary", get_health_summary))
    cors.add(add_route("GET", "/endpoints", get_endpoints_health))
    cors.add(add_route("GET", "/circuits/{circuit_id}", get_circuit_health))
    return app, []
