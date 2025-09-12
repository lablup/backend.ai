from __future__ import annotations

import time
from typing import TYPE_CHECKING, Annotated, Iterable, Sequence
from uuid import UUID

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import selectinload

from ai.backend.appproxy.common.types import (
    AppMode,
    CORSOptions,
    PydanticResponse,
    SerializableCircuit,
    WebMiddleware,
)
from ai.backend.appproxy.common.utils import pydantic_api_handler, pydantic_api_response_handler

from ..models import Circuit
from ..models.utils import execute_with_txn_retry
from ..types import RootContext
from .types import StubResponseModel
from .utils import auth_required

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


class BulkRemoveCircuitsRequestModel(BaseModel):
    circuit_ids: Annotated[list[UUID], Field(description="Comma separated list of Circuit UUIDs.")]

    @validator("circuit_ids", pre=True)
    def split_comma_separated(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            return [] if v == "" else v.split(",")
        return v


class CircuitStatisticsModel(SerializableCircuit):
    requests: int = Field(description="Number of requests processed by this circuit.")
    last_access: int | None = Field(description="Last access timestamp.")
    ttl: int | None = Field(
        description="Number of seconds remaining before this circuit will be discharged due to inactivity. Can be null if `app_mode` is `interactive`.",
    )


@auth_required("worker")
@pydantic_api_response_handler
async def get_circuit(request: web.Request) -> PydanticResponse[SerializableCircuit]:
    """
    Returns information of a circuit.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_readonly_session() as sess:
        circuit = await Circuit.get(sess, UUID(request.match_info["circuit_id"]))
        return PydanticResponse(SerializableCircuit(**circuit.dump_model()))


@auth_required("worker")
@pydantic_api_response_handler
async def delete_circuit(request: web.Request) -> PydanticResponse[StubResponseModel]:
    """
    Removes circuit record from both coordinator and worker.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async def _update(sess: SASession) -> None:
        circuit = await Circuit.get(sess, UUID(request.match_info["circuit_id"]), load_worker=True)
        circuit.worker_row.occupied_slots -= 1
        await sess.delete(circuit)
        await root_ctx.circuit_manager.unload_circuits([circuit])

    async with root_ctx.db.connect() as db_conn:
        await execute_with_txn_retry(_update, root_ctx.db.begin_session, db_conn)
    return PydanticResponse(StubResponseModel(success=True))


@auth_required("worker")
@pydantic_api_handler(BulkRemoveCircuitsRequestModel)
async def delete_circuit_bulk(
    request: web.Request, params: BulkRemoveCircuitsRequestModel
) -> PydanticResponse[StubResponseModel]:
    """
    Removes circuit record from both coordinator and worker, in bulk.
    """
    root_ctx: RootContext = request.app["_root.context"]

    async def _update(sess: SASession) -> Sequence[Circuit]:
        query = (
            sa.select(Circuit)
            .where(Circuit.id.in_(params.circuit_ids))
            .options(selectinload(Circuit.worker_row))
        )
        result = await sess.execute(query)
        circuits = result.scalars().all()

        for circuit in circuits:
            circuit.worker_row.occupied_slots -= 1
            await sess.delete(circuit)

        return circuits

    async with root_ctx.db.connect() as db_conn:
        circuits = await execute_with_txn_retry(_update, root_ctx.db.begin_session, db_conn)
    await root_ctx.circuit_manager.unload_circuits(circuits)

    return PydanticResponse(StubResponseModel(success=True))


@auth_required("worker")
@pydantic_api_response_handler
async def get_circuit_statistics(request: web.Request) -> PydanticResponse[CircuitStatisticsModel]:
    """
    Lists statical informations about given circuit.
    """
    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin_readonly_session() as sess:
        circuit = await Circuit.get(sess, UUID(request.match_info["circuit_id"]))

    last_access, requests = await root_ctx.valkey_live.get_multiple_live_data([
        f"circuit.{circuit.id}.last_access",
        f"circuit.{circuit.id}.requests",
    ])
    # Handle bytes data from valkey
    last_access_value = (
        float(last_access.decode("utf-8")) if last_access else circuit.created_at.timestamp()
    )
    requests_value = int(requests.decode("utf-8")) if requests else 0

    if circuit.app_mode != AppMode.INFERENCE:
        ttl = int(
            root_ctx.local_config.proxy_coordinator.unused_circuit_collection_timeout
            - (time.time() - last_access_value)
        )
    else:
        ttl = None
    return PydanticResponse(
        CircuitStatisticsModel(
            ttl=ttl,
            last_access=int(last_access_value * 1000),
            requests=requests_value,
            **circuit.dump_model(),
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
    app["prefix"] = "api/circuit"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    add_route = app.router.add_route
    cors.add(add_route("DELETE", "/_/bulk", delete_circuit_bulk))
    cors.add(add_route("GET", "/{circuit_id}", get_circuit))
    cors.add(add_route("GET", "/{circuit_id}/statistics", get_circuit_statistics))
    cors.add(add_route("DELETE", "/{circuit_id}", delete_circuit))
    return app, []
