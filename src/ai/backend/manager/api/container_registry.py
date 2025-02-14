from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.container_registry import (
    ContainerRegistryType,
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.exceptions import (
    ContainerRegistryWebhookAuthorizationFailed,
)
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
)
from ai.backend.manager.models.gql_models.container_registry_v2 import handle_allowed_groups_update

from .exceptions import (
    GenericBadRequest,
    HarborWebhookContainerRegistryRowNotFound,
    InternalServerError,
    ObjectNotFound,
)

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import pydantic_params_api_handler

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
    except ObjectNotFound as e:
        raise e
    except IntegrityError as e:
        raise GenericBadRequest(f"Failed to update allowed groups! Details: {str(e)}")
    except Exception as e:
        raise InternalServerError(f"Failed to update container registry! Details: {str(e)}")

    return PatchContainerRegistryResponseModel.model_validate(container_registry)


async def _get_registry_row_matching_url(
    db_sess: AsyncSession, registry_url: str, project: str
) -> ContainerRegistryRow:
    query = sa.select(ContainerRegistryRow).where(
        (ContainerRegistryRow.type == ContainerRegistryType.HARBOR2)
        & (ContainerRegistryRow.url.like(f"%{registry_url}%"))
        & (ContainerRegistryRow.project == project)
    )
    result = await db_sess.execute(query)
    return result.scalars().one_or_none()


def _is_authorized_harbor_webhook_request(
    auth_header: Optional[str], registry_row: ContainerRegistryRow
) -> bool:
    if auth_header:
        extra = registry_row.extra or {}
        return extra.get("webhook_auth_header") == auth_header
    return True


async def _handle_harbor_webhook_event(
    root_ctx: RootContext,
    event_type: str,
    registry_row: ContainerRegistryRow,
    project: str,
    img_name: str,
    tag: str,
) -> None:
    match event_type:
        # Perform image rescan only for events that require it.
        case "PUSH_ARTIFACT":
            await _handle_push_artifact_event(root_ctx, registry_row, project, img_name, tag)
        case _:
            log.debug(
                'Ignore harbor webhook event: "{}". Recommended to modify the webhook config to not subscribe to this event type.',
                event_type,
            )


async def _handle_push_artifact_event(
    root_ctx: RootContext, registry_row: ContainerRegistryRow, project: str, img_name: str, tag: str
) -> None:
    scanner = HarborRegistry_v2(root_ctx.db, registry_row.registry_name, registry_row)
    await scanner.scan_single_ref(f"{project}/{img_name}:{tag}")


class HarborWebhookRequestModel(BaseModel):
    type: str = Field(
        description="Type of the webhook event triggered by Harbor. See Harbor documentation for details."
    )

    class EventData(BaseModel):
        class Resource(BaseModel):
            resource_url: str = Field(description="URL of the artifact")
            tag: str = Field(description="Tag of the artifact")

        class Repository(BaseModel):
            namespace: str = Field(description="Harbor project (namespace)")
            name: str = Field(description="Name of the repository")

        resources: list[Resource] = Field(
            description="List of related artifacts involved in the event"
        )
        repository: Repository = Field(description="Repository details")

    event_data: EventData = Field(description="Event details")


@server_status_required(ALL_ALLOWED)
@pydantic_params_api_handler(HarborWebhookRequestModel)
async def harbor_webhook_handler(
    request: web.Request, params: HarborWebhookRequestModel
) -> web.Response:
    auth_header = request.headers.get("Authorization", None)
    event_type = params.type
    resources = params.event_data.resources
    project = params.event_data.repository.namespace
    img_name = params.event_data.repository.name
    log.info("HARBOR_WEBHOOK_HANDLER (event_type:{})", event_type)

    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin_session() as db_sess:
        for resource in resources:
            resource_url = resource.resource_url
            registry_url = resource_url.split("/")[0]

            registry_row = await _get_registry_row_matching_url(db_sess, registry_url, project)
            if not registry_row:
                raise HarborWebhookContainerRegistryRowNotFound(
                    extra_msg=f"Harbor webhook triggered, but the matching container registry row not found! (registry_url: {registry_url}, project: {project})",
                )

            if not _is_authorized_harbor_webhook_request(auth_header, registry_row):
                raise ContainerRegistryWebhookAuthorizationFailed(
                    extra_msg=f"Unauthorized webhook request (registry: {registry_row.registry_name}, project: {project})",
                )

            await _handle_harbor_webhook_event(
                root_ctx, event_type, registry_row, project, img_name, resource.tag
            )

    return web.Response(status=204)


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
