from typing import Annotated, Iterable
from uuid import UUID

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import BaseModel, Field

from ai.backend.appproxy.common.exceptions import ObjectNotFound
from ai.backend.appproxy.common.types import (
    CORSOptions,
    FrontendMode,
    PydanticResponse,
    WebMiddleware,
)
from ai.backend.appproxy.common.utils import (
    pydantic_api_handler,
    pydantic_api_response_handler,
)

from ..models import Circuit, StaticAddress
from ..models.utils import execute_with_txn_retry
from ..types import RootContext
from .types import StubResponseModel
from .utils import auth_required


class StaticAddressCreateRequestModel(BaseModel):
    frontend_mode: Annotated[
        FrontendMode,
        Field(description="Frontend mode - either 'port' or 'wildcard'"),
    ]
    port: Annotated[
        int | None, Field(default=None, description="Port number (required for port mode)")
    ]
    subdomain: Annotated[
        str | None, Field(default=None, description="Subdomain name (required for wildcard mode)")
    ]
    name: Annotated[
        str | None,
        Field(default=None, description="Optional human-readable name for the static address"),
    ]
    description: Annotated[
        str | None,
        Field(default=None, description="Optional description of the static address"),
    ]


class StaticAddressResponseModel(BaseModel):
    id: UUID
    frontend_mode: FrontendMode
    port: int | None
    subdomain: str | None
    is_allocated: bool
    allocated_to_circuit: UUID | None
    name: str | None
    description: str | None
    address_display: str


class StaticAddressListResponseModel(BaseModel):
    static_addresses: list[StaticAddressResponseModel]


@auth_required("manager")
@pydantic_api_handler(StaticAddressCreateRequestModel)
async def create_static_address(
    request: web.Request, params: StaticAddressCreateRequestModel
) -> PydanticResponse[StaticAddressResponseModel]:
    """
    Creates a new static address that can be allocated to circuits.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async def _create(sess) -> StaticAddress:
        # Check for existing address conflicts
        try:
            existing = await StaticAddress.find_by_address(
                sess, params.frontend_mode, params.port, params.subdomain
            )
            raise ValueError(f"Static address already exists: {existing.address_display}")
        except ObjectNotFound:
            pass  # This is what we want - no existing address

        # Create the static address
        static_address = StaticAddress.create(
            frontend_mode=params.frontend_mode,
            port=params.port,
            subdomain=params.subdomain,
            name=params.name,
            description=params.description,
        )
        sess.add(static_address)
        await sess.flush()
        return static_address

    async with root_ctx.db.connect() as db_conn:
        static_address = await execute_with_txn_retry(_create, root_ctx.db.begin_session, db_conn)

    return PydanticResponse(
        StaticAddressResponseModel(
            id=static_address.id,
            frontend_mode=static_address.frontend_mode,
            port=static_address.port,
            subdomain=static_address.subdomain,
            is_allocated=static_address.is_allocated,
            allocated_to_circuit=static_address.allocated_to_circuit,
            name=static_address.name,
            description=static_address.description,
            address_display=static_address.address_display,
        )
    )


@auth_required("manager")
@pydantic_api_response_handler
async def get_static_address(
    request: web.Request,
) -> PydanticResponse[StaticAddressResponseModel]:
    """
    Retrieves information about a specific static address.
    """
    root_ctx: RootContext = request.app["_root.context"]
    static_address_id = UUID(request.match_info["static_address_id"])

    async def _get(sess) -> StaticAddress:
        return await StaticAddress.get(sess, static_address_id, load_circuit=True)

    async with root_ctx.db.connect() as db_conn:
        static_address = await execute_with_txn_retry(
            _get, root_ctx.db.begin_readonly_session, db_conn
        )

    return PydanticResponse(
        StaticAddressResponseModel(
            id=static_address.id,
            frontend_mode=static_address.frontend_mode,
            port=static_address.port,
            subdomain=static_address.subdomain,
            is_allocated=static_address.is_allocated,
            allocated_to_circuit=static_address.allocated_to_circuit,
            name=static_address.name,
            description=static_address.description,
            address_display=static_address.address_display,
        )
    )


@auth_required("manager")
@pydantic_api_response_handler
async def list_static_addresses(
    request: web.Request,
) -> PydanticResponse[StaticAddressListResponseModel]:
    """
    Lists all static addresses, with optional filtering.
    """
    root_ctx: RootContext = request.app["_root.context"]

    # Parse query parameters
    allocated_only = request.query.get("allocated_only", "false").lower() == "true"
    available_only = request.query.get("available_only", "false").lower() == "true"

    async def _list(sess) -> list[StaticAddress]:
        result = await StaticAddress.list_static_addresses(
            sess,
            load_circuit=True,
            allocated_only=allocated_only,
            available_only=available_only,
        )
        return list(result)

    async with root_ctx.db.connect() as db_conn:
        static_addresses = await execute_with_txn_retry(
            _list, root_ctx.db.begin_readonly_session, db_conn
        )

    return PydanticResponse(
        StaticAddressListResponseModel(
            static_addresses=[
                StaticAddressResponseModel(
                    id=addr.id,
                    frontend_mode=addr.frontend_mode,
                    port=addr.port,
                    subdomain=addr.subdomain,
                    is_allocated=addr.is_allocated,
                    allocated_to_circuit=addr.allocated_to_circuit,
                    name=addr.name,
                    description=addr.description,
                    address_display=addr.address_display,
                )
                for addr in static_addresses
            ]
        )
    )


@auth_required("manager")
@pydantic_api_response_handler
async def delete_static_address(
    request: web.Request,
) -> PydanticResponse[StubResponseModel]:
    """
    Deletes a static address. The address must not be currently allocated to a circuit.
    """
    root_ctx: RootContext = request.app["_root.context"]
    static_address_id = UUID(request.match_info["static_address_id"])

    async def _delete(sess) -> None:
        static_address = await StaticAddress.get(sess, static_address_id, load_circuit=True)

        if static_address.is_allocated:
            # Get endpoint information for better error message
            circuit = static_address.circuit
            endpoint_info = ""
            if circuit and circuit.endpoint_id:
                endpoint_info = f" (endpoint {circuit.endpoint_id})"
            elif circuit:
                endpoint_info = f" (circuit {circuit.id})"

            raise ValueError(
                f"Cannot delete static address {static_address_id}: "
                f"currently allocated to circuit {static_address.allocated_to_circuit}"
                f"{endpoint_info}. Use the disassociate API first to release the address."
            )

        await sess.delete(static_address)

    async with root_ctx.db.connect() as db_conn:
        await execute_with_txn_retry(_delete, root_ctx.db.begin_session, db_conn)
    return PydanticResponse(StubResponseModel(success=True))


class StaticAddressUpdateRequestModel(BaseModel):
    name: Annotated[
        str | None,
        Field(default=None, description="Optional human-readable name for the static address"),
    ]
    description: Annotated[
        str | None,
        Field(default=None, description="Optional description of the static address"),
    ]


@auth_required("manager")
@pydantic_api_handler(StaticAddressUpdateRequestModel)
async def update_static_address(
    request: web.Request, params: StaticAddressUpdateRequestModel
) -> PydanticResponse[StaticAddressResponseModel]:
    """
    Updates metadata for a static address (name and description only).
    """
    root_ctx: RootContext = request.app["_root.context"]
    static_address_id = UUID(request.match_info["static_address_id"])

    async def _update(sess) -> StaticAddress:
        static_address = await StaticAddress.get(sess, static_address_id)

        if params.name is not None:
            static_address.name = params.name
        if params.description is not None:
            static_address.description = params.description

        static_address.updated_at = sa.func.now()
        await sess.flush()
        return static_address

    async with root_ctx.db.connect() as db_conn:
        static_address = await execute_with_txn_retry(_update, root_ctx.db.begin_session, db_conn)

    return PydanticResponse(
        StaticAddressResponseModel(
            id=static_address.id,
            frontend_mode=static_address.frontend_mode,
            port=static_address.port,
            subdomain=static_address.subdomain,
            is_allocated=static_address.is_allocated,
            allocated_to_circuit=static_address.allocated_to_circuit,
            name=static_address.name,
            description=static_address.description,
            address_display=static_address.address_display,
        )
    )


class EndpointAssociationRequestModel(BaseModel):
    endpoint_id: Annotated[
        UUID,
        Field(description="ID of the endpoint to associate with this static address"),
    ]


@auth_required("manager")
@pydantic_api_handler(EndpointAssociationRequestModel)
async def associate_endpoint(
    request: web.Request, params: EndpointAssociationRequestModel
) -> PydanticResponse[StubResponseModel]:
    """
    Associates a static address with an existing endpoint.
    The endpoint must not already be using a static address.
    """
    root_ctx: RootContext = request.app["_root.context"]
    static_address_id = UUID(request.match_info["static_address_id"])

    async def _associate(sess) -> None:
        # Get the static address
        static_address = await StaticAddress.get(sess, static_address_id)
        if static_address.is_allocated:
            raise ValueError(
                f"Static address {static_address_id} is already allocated to circuit {static_address.allocated_to_circuit}"
            )

        # Get the circuit/endpoint
        circuit = await Circuit.find_by_endpoint(sess, params.endpoint_id, load_worker=True)
        if circuit.static_address_id:
            raise ValueError(
                f"Endpoint {params.endpoint_id} is already using static address {circuit.static_address_id}"
            )

        # Verify compatibility
        if circuit.worker_row.frontend_mode != static_address.frontend_mode:
            raise ValueError(
                f"Endpoint frontend mode {circuit.worker_row.frontend_mode} incompatible with "
                f"static address frontend mode {static_address.frontend_mode}"
            )

        # Update allocations
        await static_address.allocate_to_circuit(circuit.id)
        circuit.static_address_id = static_address.id

        # Clear old address info since we're now using static address
        circuit.port = None
        circuit.subdomain = None

        # Update circuit routing
        await root_ctx.circuit_manager.update_circuit_routes(circuit, circuit.route_info)

    async with root_ctx.db.connect() as db_conn:
        await execute_with_txn_retry(_associate, root_ctx.db.begin_session, db_conn)
    return PydanticResponse(StubResponseModel(success=True))


@auth_required("manager")
@pydantic_api_response_handler
async def disassociate_endpoint(
    request: web.Request,
) -> PydanticResponse[StubResponseModel]:
    """
    Disassociates a static address from its current endpoint.
    The endpoint will revert to dynamic address allocation.
    """
    root_ctx: RootContext = request.app["_root.context"]
    static_address_id = UUID(request.match_info["static_address_id"])

    async def _disassociate(sess) -> None:
        # Get the static address
        static_address = await StaticAddress.get(sess, static_address_id, load_circuit=True)
        if not static_address.is_allocated:
            raise ValueError(f"Static address {static_address_id} is not currently allocated")

        # Get the circuit
        circuit = static_address.circuit
        if not circuit:
            raise ValueError(f"Static address {static_address_id} allocation is inconsistent")

        # Store the worker for address reallocation
        worker = circuit.worker_row

        # Deallocate static address
        await static_address.deallocate()
        circuit.static_address_id = None

        # Reallocate dynamic address based on worker type
        if worker.frontend_mode == FrontendMode.WILDCARD_DOMAIN:
            # Generate new subdomain
            import uuid

            acquired_subdomains = [c.subdomain for c in worker.circuits if c.id != circuit.id]
            sub_id = str(uuid.uuid4()).split("-")[0]
            subdomain = f"app-{sub_id}"
            while subdomain in acquired_subdomains:
                sub_id = str(uuid.uuid4()).split("-")[0]
                subdomain = f"app-{sub_id}"
            circuit.subdomain = subdomain
        else:
            # Find available port
            acquired_ports = set([c.port for c in worker.circuits if c.id != circuit.id])
            port_range = worker.port_range
            if not port_range:
                raise ValueError("Worker has no available port range")
            port_pool = set(range(port_range[0], port_range[1] + 1)) - acquired_ports
            if len(port_pool) == 0:
                raise ValueError("No available ports in worker port range")
            circuit.port = port_pool.pop()

        # Update circuit routing
        await root_ctx.circuit_manager.update_circuit_routes(circuit, circuit.route_info)

    async with root_ctx.db.connect() as db_conn:
        await execute_with_txn_retry(_disassociate, root_ctx.db.begin_session, db_conn)
    return PydanticResponse(StubResponseModel(success=True))


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v2/static-addresses"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(app.router.add_resource(r""))
    cors.add(add_route("POST", "", create_static_address))
    cors.add(add_route("GET", "", list_static_addresses))
    cors.add(add_route("GET", "/{static_address_id}", get_static_address))
    cors.add(add_route("PUT", "/{static_address_id}", update_static_address))
    cors.add(add_route("DELETE", "/{static_address_id}", delete_static_address))
    cors.add(add_route("POST", "/{static_address_id}/associate", associate_endpoint))
    cors.add(add_route("DELETE", "/{static_address_id}/associate", disassociate_endpoint))
    return app, []
