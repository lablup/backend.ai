from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Iterable, Tuple

import aiohttp_cors
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from sqlalchemy.exc import IntegrityError

from ai.backend.common.container_registry import (
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
)
from ai.backend.manager.models.gql_models.container_registry_v2 import handle_allowed_groups_update

from .exceptions import ContainerRegistryNotFound, GenericBadRequest, InternalServerError

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params, pydantic_params_api_handler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@server_status_required(READ_ALLOWED)
@superadmin_required
@pydantic_params_api_handler(PatchContainerRegistryRequestModel)
async def patch_container_registry(
    request: web.Request, params: PatchContainerRegistryRequestModel
) -> PatchContainerRegistryResponseModel:
    from ..models.container_registry import ContainerRegistryRow

    registry_id = uuid.UUID(request.match_info["registry_id"])
    log.info("PATCH_CONTAINER_REGISTRY (registry:{})", registry_id)
    root_ctx: RootContext = request.app["_root.context"]
    registry_row_updates = params.model_dump(exclude={"allowed_groups"}, exclude_none=True)

    try:
        async with root_ctx.db.begin_session() as db_session:
            if registry_row_updates:
                update_stmt = (
                    sa.update(ContainerRegistryRow)
                    .where(ContainerRegistryRow.id == registry_id)
                    .values(registry_row_updates)
                )
                await db_session.execute(update_stmt)

            query = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
            container_registry = (await db_session.execute(query)).fetchone()[0]

        if params.allowed_groups:
            await handle_allowed_groups_update(root_ctx.db, registry_id, params.allowed_groups)
    except ContainerRegistryNotFound as e:
        raise e
    except IntegrityError as e:
        raise GenericBadRequest(f"Failed to update allowed groups! Details: {str(e)}")
    except Exception as e:
        raise InternalServerError(f"Failed to update container registry! Details: {str(e)}")

    return PatchContainerRegistryResponseModel.model_validate(container_registry)


@server_status_required(ALL_ALLOWED)
@check_api_params(t.Mapping(t.String, t.Any))
async def harbor_webhook_handler(request: web.Request, params: Any) -> web.Response:
    event_type = params["type"]
    resources = params["event_data"]["resources"]
    project = params["event_data"]["repository"]["namespace"]
    img_name = params["event_data"]["repository"]["name"]
    log.info("HARBOR_WEBHOOK_HANDLER (type:{})", event_type)

    root_ctx: RootContext = request.app["_root.context"]

    async with root_ctx.db.begin_session() as db_sess:
        for resource in resources:
            resource_url = resource["resource_url"]
            registry_url = resource_url.split("/")[0]

            registry_row = (
                await db_sess.execute(
                    sa.select([ContainerRegistryRow]).where(
                        (ContainerRegistryRow.project == project)
                        & (ContainerRegistryRow.url.like(f"%{registry_url}%"))
                    )
                )
            ).fetchone()[0]

            match event_type:
                # Perform image rescan only for events that require it.
                case "PUSH_ARTIFACT":
                    scanner_cls = HarborRegistry_v2
                    scanner = scanner_cls(root_ctx.db, project, registry_row)
                    img_tag = resource["tag"]
                    await scanner.scan_single_ref(project + "/" + img_name + ":" + img_tag)
                case "DELETE_ARTIFACT":
                    # TODO: Delete image row directly
                    pass
                case _:
                    pass

    return web.json_response({})


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "container-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route("PATCH", "/{registry_id}", patch_container_registry))
    cors.add(app.router.add_route("POST", "/webhook/harbor", harbor_webhook_handler))
    return app, []
