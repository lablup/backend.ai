import json
import logging
from datetime import datetime
from typing import Annotated, Iterable
from uuid import UUID

import aiohttp_cors
from aiohttp import web
from pydantic import BaseModel, Field

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
from .utils import auth_required

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class SlotResponseModel(BaseModel):
    rel: Annotated[UUID, Field(description="Circuit ID.")]
    port: Annotated[int | None, Field(description="Port number.")]
    subdomain: Annotated[str | None, Field(default=None, description="Subdomain for the circuit.")]
    wsproxy_version: Annotated[str, Field(description="AppProxy version.")]
    worker__authority: Annotated[str, Field(description="Authority name of the worker.")]
    circuit__app: Annotated[str, Field(description="App name.")]
    circuit__session_id: Annotated[
        UUID | None, Field(default=None, description="Session ID of the circuit.")
    ]
    circuit__open_to_public: Annotated[
        bool, Field(description="Whether the circuit is open to public.")
    ]
    circuit__allowed_client_ips: Annotated[
        str | None, Field(default=None, description="Allowed client IPs for the circuit.")
    ]
    circuit__envs: Annotated[
        str | None, Field(default=None, description="Environment variables for the circuit.")
    ]
    circuit__arguments: Annotated[
        str | None, Field(default=None, description="Arguments for the circuit.")
    ]
    circuit__created: Annotated[datetime, Field(description="Creation time of the circuit.")]
    circuit__modified: Annotated[
        datetime, Field(description="Last modification time of the circuit.")
    ]


@auth_required("worker")
@pydantic_api_response_handler
async def list_slots(request: web.Request) -> PydanticResponse[list[SlotResponseModel]]:
    """
    Lists all slots.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        circuits = await Circuit.list_circuits(sess, load_worker=True)
        return PydanticResponse([
            SlotResponseModel(
                port=c.port,
                rel=c.id,
                subdomain=c.subdomain,
                wsproxy_version="v2",
                worker__authority=c.worker_row.authority,
                circuit__app=c.app,
                circuit__session_id=c.session_ids[0] if c.session_ids else None,
                circuit__open_to_public=c.open_to_public,
                circuit__allowed_client_ips=c.allowed_client_ips,
                circuit__envs=json.dumps(c.envs) if c.envs else None,
                circuit__arguments=c.arguments,
                circuit__created=c.created_at,
                circuit__modified=c.updated_at,
            )
            for c in circuits
        ])


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v1/api/slots"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_slots))
    return app, []
