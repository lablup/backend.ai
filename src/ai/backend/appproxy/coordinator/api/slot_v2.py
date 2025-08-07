import dataclasses
from typing import Annotated, Iterable

import aiohttp_cors
from aiohttp import web
from pydantic import BaseModel, Field

from ai.backend.appproxy.common.types import CORSOptions, PydanticResponse, WebMiddleware
from ai.backend.appproxy.common.utils import pydantic_api_handler

from ..models.worker import Worker
from ..types import RootContext
from .types import SlotModel
from .utils import auth_required


class ListSlotsRequestModel(BaseModel):
    wsproxy_host: Annotated[
        str | None,
        Field(
            default=None,
            description="Authority string (not UUID) of AppProxy worker. If not set, API will return slots of every workers.",
        ),
    ]
    in_use: Annotated[
        bool,
        Field(default=True, description="If set true, only returns information of occupied slots."),
    ]


class ListSlotsResponseModel(BaseModel):
    slots: list[SlotModel]


@auth_required("worker")
@pydantic_api_handler(ListSlotsRequestModel)
async def slots(
    request: web.Request, params: ListSlotsRequestModel
) -> PydanticResponse[ListSlotsResponseModel]:
    """
    Provides slot information hosted by worker mentioned.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        if _authority := params.wsproxy_host:
            workers = [await Worker.find_by_authority(sess, _authority, load_circuits=True)]
        else:
            workers = await Worker.list_workers(sess, load_circuits=True)
        slots: list[SlotModel] = []

        for worker in workers:
            slots += [
                SlotModel(**dataclasses.asdict(s))
                for s in (await worker.list_slots(sess))
                if s.in_use or (not params.in_use)
            ]

    return PydanticResponse(ListSlotsResponseModel(slots=slots))


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "api/slots"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r""))
    cors.add(root_resource.add_route("GET", slots))
    return app, []
