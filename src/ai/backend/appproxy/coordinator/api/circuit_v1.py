import logging
from typing import Iterable
from uuid import UUID

import aiohttp_cors
from aiohttp import web

from ai.backend.appproxy.common.types import (
    CORSOptions,
    PydanticResponse,
    WebMiddleware,
)
from ai.backend.appproxy.common.utils import (
    pydantic_api_response_handler,
)
from ai.backend.logging import BraceStyleAdapter

from ..models import Circuit
from ..types import RootContext
from .types import StubResponseModel
from .utils import auth_required

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@auth_required("worker")
@pydantic_api_response_handler
async def clear_circuit(request: web.Request) -> PydanticResponse[StubResponseModel]:
    """
    Breaks the circuit forcefully.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_session() as sess:
        circuit_id = UUID(request.match_info["circuit_id"])
        circuit = await Circuit.get(sess, circuit_id, load_worker=True)

        await root_ctx.circuit_manager.unload_circuits([circuit])

        circuit.worker_row.occupied_slots -= 1
        await sess.delete(circuit)

        await sess.commit()

        log.info(
            "clear_circuit(c: {}): removed circuit by request", request.match_info["circuit_id"]
        )
        return PydanticResponse(StubResponseModel(success=True))


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v1/api/circuit"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("DELETE", "/{circuit_id}", clear_circuit))
    return app, []
