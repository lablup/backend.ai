import logging
from datetime import datetime
from typing import Annotated, Iterable

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

from ..models import Worker
from ..types import RootContext
from .utils import auth_required

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class WorkerResponseModel(BaseModel):
    authority: Annotated[str, Field(description="authority name of worker.")]
    endpoint: Annotated[str, Field(description="API Endpoint of the worker.")]

    total_slots: Annotated[
        int, Field(description="Total number of slots. Set to -1 if worker is in wildcard mode.")
    ]
    ports_in_use: Annotated[int, Field(description="Number of ports in use currently.")]

    min_range: Annotated[
        int | None,
        Field(
            default=None,
            description="Start range of the app port pool. Effective only for port mode worker.",
        ),
    ]
    max_range: Annotated[
        int | None,
        Field(
            default=None,
            description="End range of the app port pool. Effective only for port mode worker.",
        ),
    ]
    wildcard_domain: Annotated[
        str | None,
        Field(
            default=None,
            description="Base domain for worker apps. Effective only for wildcard worker.",
        ),
    ]

    created: datetime
    updated: datetime


@auth_required("worker")
@pydantic_api_response_handler
async def list_workers(request: web.Request) -> PydanticResponse[list[WorkerResponseModel]]:
    """
    Lists all workers recognized by coordinator.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        workers = await Worker.list_workers(sess, load_circuits=True)
        return PydanticResponse([
            WorkerResponseModel(
                authority=w.authority,
                endpoint=str(w.api_endpoint),
                total_slots=(w.port_range[1] - w.port_range[0] + 1) if w.port_range else -1,
                ports_in_use=len(w.circuits),
                min_range=w.port_range[0] if w.port_range else None,
                max_range=w.port_range[1] if w.port_range else None,
                wildcard_domain=w.wildcard_domain,
                created=w.created_at,
                updated=w.updated_at,
            )
            for w in workers
        ])


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "v1/api/worker"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", list_workers))
    return app, []
