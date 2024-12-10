from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterable, Optional, Tuple

import aiohttp_cors
import sqlalchemy as sa
import trafaret as t
from aiohttp import web
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common import validators as tx
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.exceptions import (
    ContainerRegistryWebhookAuthorizationFailed,
    InternalServerError,
)
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow, ContainerRegistryType

from .exceptions import ContainerRegistryNotFound, GenericBadRequest

if TYPE_CHECKING:
    from .context import RootContext

from .auth import superadmin_required
from .manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["registry_id", "registry"]): t.String,
        tx.AliasedKey(["group_id", "group"]): t.String,
    })
)
async def associate_with_group(request: web.Request, params: Any) -> web.Response:
    log.info("ASSOCIATE_WITH_GROUP (cr:{}, gr:{})", params["registry_id"], params["group_id"])
    root_ctx: RootContext = request.app["_root.context"]
    registry_id = params["registry_id"]
    group_id = params["group_id"]

    async with root_ctx.db.begin_session() as db_sess:
        insert_query = sa.insert(AssociationContainerRegistriesGroupsRow).values({
            "registry_id": registry_id,
            "group_id": group_id,
        })

        try:
            await db_sess.execute(insert_query)
        except IntegrityError:
            raise GenericBadRequest("Association already exists.")

    return web.json_response({})


@server_status_required(READ_ALLOWED)
@superadmin_required
@check_api_params(
    t.Dict({
        tx.AliasedKey(["registry_id", "registry"]): t.String,
        tx.AliasedKey(["group_id", "group"]): t.String,
    })
)
async def disassociate_with_group(request: web.Request, params: Any) -> web.Response:
    log.info("DISASSOCIATE_WITH_GROUP (cr:{}, gr:{})", params["registry_id"], params["group_id"])
    root_ctx: RootContext = request.app["_root.context"]
    registry_id = params["registry_id"]
    group_id = params["group_id"]

    async with root_ctx.db.begin_session() as db_sess:
        delete_query = (
            sa.delete(AssociationContainerRegistriesGroupsRow)
            .where(AssociationContainerRegistriesGroupsRow.registry_id == registry_id)
            .where(AssociationContainerRegistriesGroupsRow.group_id == group_id)
        )

        result = await db_sess.execute(delete_query)
        if result.rowcount == 0:
            raise ContainerRegistryNotFound()

    return web.json_response({})


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


@server_status_required(ALL_ALLOWED)
@check_api_params(
    t.Dict({
        "type": t.String,
        "event_data": t.Dict({
            "resources": t.List(
                t.Dict({
                    "resource_url": t.String,
                    "tag": t.String,
                }).allow_extra("*")
            ),
            "repository": t.Dict({
                "namespace": t.String,
                "name": t.String,
            }).allow_extra("*"),
        }).allow_extra("*"),
    }).allow_extra("*")
)
async def harbor_webhook_handler(request: web.Request, params: Any) -> web.Response:
    auth_header = request.headers.get("Authorization", None)
    event_type = params["type"]
    resources = params["event_data"]["resources"]
    project = params["event_data"]["repository"]["namespace"]
    img_name = params["event_data"]["repository"]["name"]
    log.info("HARBOR_WEBHOOK_HANDLER (event_type:{})", event_type)

    root_ctx: RootContext = request.app["_root.context"]
    async with root_ctx.db.begin_session() as db_sess:
        for resource in resources:
            resource_url = resource["resource_url"]
            registry_url = resource_url.split("/")[0]

            registry_row = await _get_registry_row_matching_url(db_sess, registry_url, project)
            if not registry_row:
                raise InternalServerError(
                    extra_msg=f"Harbor webhook triggered, but the matching container registry row not found! (registry_url: {registry_url}, project: {project})",
                )

            if not _is_authorized_harbor_webhook_request(auth_header, registry_row):
                raise ContainerRegistryWebhookAuthorizationFailed(
                    extra_msg=f"Unauthorized webhook request (registry: {registry_row.registry_name}, project: {project})",
                )

            await _handle_harbor_webhook_event(
                root_ctx, event_type, registry_row, project, img_name, resource["tag"]
            )

    return web.json_response({})


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4, 5)
    app["prefix"] = "container-registries"
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)

    cors.add(app.router.add_route("POST", "/webhook/harbor", harbor_webhook_handler))
    cors.add(app.router.add_route("POST", "/associate-with-group", associate_with_group))
    cors.add(app.router.add_route("POST", "/disassociate-with-group", disassociate_with_group))
    return app, []
