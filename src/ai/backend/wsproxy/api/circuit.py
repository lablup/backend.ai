from typing import Iterable
from uuid import UUID

import aiohttp_cors
from aiohttp import web

from ai.backend.wsproxy.types import (
    CORSOptions,
    PydanticResponse,
    WebMiddleware,
)

from ..defs import RootContext
from ..exceptions import ObjectNotFound
from .types import StubResponseModel
from .utils import auth_required, pydantic_api_response_handler


@auth_required("worker")
@pydantic_api_response_handler
async def delete_circuit(request: web.Request) -> PydanticResponse[StubResponseModel]:
    """
    Removes circuit record from wsproxy.
    """
    root_ctx: RootContext = request.app["_root.context"]
    circuit_id = UUID(request.match_info["circuit_id"])

    try:
        circuit = root_ctx.proxy_frontend.circuits[circuit_id]
    except KeyError:
        raise ObjectNotFound(object_name="Circuit")
    await root_ctx.proxy_frontend.break_circuit(circuit)

    return PydanticResponse(StubResponseModel(success=True))


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "api/circuit"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route("DELETE", "/{circuit_id}", delete_circuit))
    return app, []
