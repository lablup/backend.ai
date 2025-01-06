from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterable, Tuple

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import AliasChoices, BaseModel, Field
from sqlalchemy.exc import IntegrityError

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)

from .exceptions import ContainerRegistryNotFound, GenericBadRequest

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import pydantic_params_api_handler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AssociationRequestModel(BaseModel):
    registry_id: str = Field(
        validation_alias=AliasChoices("registry_id", "registry"),
        description="Container registry row's ID",
    )
    group_id: str = Field(
        validation_alias=AliasChoices("group_id", "group"),
        description="Group row's ID",
    )


@server_status_required(READ_ALLOWED)
@superadmin_required
@pydantic_params_api_handler(AssociationRequestModel)
async def associate_with_group(
    request: web.Request, params: AssociationRequestModel
) -> web.Response:
    log.info("ASSOCIATE_WITH_GROUP (cr:{}, gr:{})", params.registry_id, params.group_id)
    root_ctx: RootContext = request.app["_root.context"]
    registry_id = params.registry_id
    group_id = params.group_id

    async with root_ctx.db.begin_session() as db_sess:
        insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values({
            "registry_id": registry_id,
            "group_id": group_id,
        })

        try:
            await db_sess.execute(insert_query)
        except IntegrityError:
            raise GenericBadRequest("Association already exists.")

    return web.Response(status=204)


class DisassociationRequestModel(BaseModel):
    registry_id: str = Field(
        validation_alias=AliasChoices("registry_id", "registry"),
        description="Container registry row's ID",
    )
    group_id: str = Field(
        validation_alias=AliasChoices("group_id", "group"),
        description="Group row's ID",
    )


@server_status_required(READ_ALLOWED)
@superadmin_required
@pydantic_params_api_handler(DisassociationRequestModel)
async def disassociate_with_group(
    request: web.Request, params: DisassociationRequestModel
) -> web.Response:
    log.info("DISASSOCIATE_WITH_GROUP (cr:{}, gr:{})", params.registry_id, params.group_id)
    root_ctx: RootContext = request.app["_root.context"]
    registry_id = params.registry_id
    group_id = params.group_id

    async with root_ctx.db.begin_session() as db_sess:
        delete_query = (
            sa.delete(AssociationContainerRegistriesGroupsRow)
            .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
            .where(AssociationContainerRegistriesGroupsRow.group_id == group_id)
        )

        result = await db_sess.execute(delete_query)
        if result.rowcount == 0:
            raise ContainerRegistryNotFound()

    return web.Response(status=204)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "container-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("POST", "/associate-with-group", associate_with_group))
    cors.add(app.router.add_route("POST", "/disassociate-with-group", disassociate_with_group))
    return app, []
