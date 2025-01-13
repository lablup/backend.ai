from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, Iterable, Optional, Tuple

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow, ContainerRegistryType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .exceptions import ContainerRegistryNotFound, GenericBadRequest, InternalServerError

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import pydantic_params_api_handler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AllowedGroups(BaseModel):
    add: list[str] = []
    remove: list[str] = []


class ContainerRegistryRowSchema(BaseModel):
    id: Optional[uuid.UUID] = None
    url: Optional[str] = None
    registry_name: Optional[str] = None
    type: Optional[ContainerRegistryType] = None
    project: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_verify: Optional[bool] = None
    is_global: Optional[bool] = None
    extra: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class PatchContainerRegistryRequestModel(ContainerRegistryRowSchema):
    allowed_groups: Optional[AllowedGroups] = None


class PatchContainerRegistryResponseModel(ContainerRegistryRowSchema):
    pass


async def handle_allowed_groups_update(
    db: ExtendedAsyncSAEngine, registry_id: uuid.UUID, allowed_group_updates: AllowedGroups
):
    async with db.begin_session() as db_sess:
        if allowed_group_updates.add:
            insert_values = [
                {"registry_id": registry_id, "group_id": group_id}
                for group_id in allowed_group_updates.add
            ]

            insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values(insert_values)
            await db_sess.execute(insert_query)

        if allowed_group_updates.remove:
            delete_query = (
                sa.delete(AssociationContainerRegistriesGroupsRow)
                .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
                .where(
                    AssociationContainerRegistriesGroupsRow.group_id.in_(
                        allowed_group_updates.remove
                    )
                )
            )
            result = await db_sess.execute(delete_query)
            if result.rowcount == 0:
                raise ContainerRegistryNotFound()


@server_status_required(READ_ALLOWED)
@superadmin_required
@pydantic_params_api_handler(PatchContainerRegistryRequestModel)
async def patch_container_registry(
    request: web.Request, params: PatchContainerRegistryRequestModel
) -> PatchContainerRegistryResponseModel:
    registry_id = uuid.UUID(request.match_info["registry_id"])
    log.info("PATCH_CONTAINER_REGISTRY (cr:{})", registry_id)
    root_ctx: RootContext = request.app["_root.context"]
    registry_row_updates = params.model_dump(exclude={"allowed_groups"}, exclude_none=True)

    if registry_row_updates:
        try:
            async with root_ctx.db.begin_session() as db_session:
                update_stmt = (
                    sa.update(ContainerRegistryRow)
                    .where(ContainerRegistryRow.id == registry_id)
                    .values(registry_row_updates)
                )
                await db_session.execute(update_stmt)

                select_stmt = sa.select(ContainerRegistryRow).where(
                    ContainerRegistryRow.id == registry_id
                )
                updated_container_registry = (await db_session.execute(select_stmt)).fetchone()[0]
        except Exception as e:
            raise InternalServerError(f"Failed to update container registry! Details: {str(e)}")

    try:
        if params.allowed_groups:
            await handle_allowed_groups_update(root_ctx.db, registry_id, params.allowed_groups)
    except ContainerRegistryNotFound as e:
        raise e
    except IntegrityError as e:
        raise GenericBadRequest(f"Failed to update allowed groups! Details: {str(e)}")
    except Exception as e:
        raise InternalServerError(f"Failed to update allowed groups! Details: {str(e)}")

    return PatchContainerRegistryResponseModel.model_validate(updated_container_registry)


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "container-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("PATCH", "/{registry_id}", patch_container_registry))
    return app, []
