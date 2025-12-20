from __future__ import annotations

import logging
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

import aiohttp_cors
import sqlalchemy as sa
from aiohttp import web
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.api_handlers import BaseFieldModel
from ai.backend.common.container_registry import (
    ContainerRegistryType,
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.errors.image import (
    ContainerRegistryWebhookAuthorizationFailed,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryRow,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
)
from ai.backend.manager.services.container_registry.actions.modify_container_registry import (
    ModifyContainerRegistryAction,
)
from ai.backend.manager.types import OptionalState, TriState

from ..errors.image import HarborWebhookContainerRegistryRowNotFound

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import LegacyBaseRequestModel, pydantic_params_api_handler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@server_status_required(READ_ALLOWED)
@superadmin_required
@pydantic_params_api_handler(PatchContainerRegistryRequestModel)
async def patch_container_registry(
    request: web.Request, params: PatchContainerRegistryRequestModel
) -> PatchContainerRegistryResponseModel:
    registry_id = uuid.UUID(request.match_info["registry_id"])
    log.info("PATCH_CONTAINER_REGISTRY (registry:{})", registry_id)
    root_ctx: RootContext = request.app["_root.context"]

    updater_spec = ContainerRegistryUpdaterSpec(
        url=OptionalState.update(params.url) if params.url is not None else OptionalState.nop(),
        registry_name=OptionalState.update(params.registry_name)
        if params.registry_name is not None
        else OptionalState.nop(),
        type=OptionalState.update(params.type) if params.type is not None else OptionalState.nop(),
        project=TriState.update(params.project) if params.project is not None else TriState.nop(),
        username=TriState.update(params.username)
        if params.username is not None
        else TriState.nop(),
        password=TriState.update(params.password)
        if params.password is not None
        else TriState.nop(),
        ssl_verify=TriState.update(params.ssl_verify)
        if params.ssl_verify is not None
        else TriState.nop(),
        is_global=TriState.update(params.is_global)
        if params.is_global is not None
        else TriState.nop(),
        extra=TriState.update(params.extra) if params.extra is not None else TriState.nop(),
        allowed_groups=TriState.update(params.allowed_groups)
        if params.allowed_groups is not None
        else TriState.nop(),
    )
    result = (
        await root_ctx.processors.container_registry.modify_container_registry.wait_for_complete(
            ModifyContainerRegistryAction(updater=Updater(spec=updater_spec, pk_value=registry_id))
        )
    )

    return PatchContainerRegistryResponseModel(
        id=result.data.id,
        url=result.data.url,
        registry_name=result.data.registry_name,
        type=result.data.type,
        project=result.data.project,
        username=result.data.username,
        password=result.data.password,
        ssl_verify=result.data.ssl_verify,
        is_global=result.data.is_global,
        extra=result.data.extra,
    )


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


class HarborWebhookRequestModel(LegacyBaseRequestModel):
    type: str = Field(
        description="Type of the webhook event triggered by Harbor. See Harbor documentation for details."
    )

    class EventData(BaseFieldModel):
        class Resource(BaseFieldModel):
            resource_url: str = Field(description="URL of the artifact")
            tag: str = Field(description="Tag of the artifact")

        class Repository(BaseFieldModel):
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

    return web.Response(status=HTTPStatus.NO_CONTENT)


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
