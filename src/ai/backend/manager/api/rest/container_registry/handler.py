"""Container registry handler using the new ApiHandler pattern.

All handlers use typed parameters (``BodyParam``, ``PathParam``,
``RequestCtx``, ``ProcessorsCtx``) that are automatically extracted by
``_wrap_api_handler``, and responses are returned as ``APIResponse``
objects.
"""

from __future__ import annotations

import logging
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import sqlalchemy as sa

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.container_registry import (
    ContainerRegistryType,
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.common.dto.manager.registry.request import HarborWebhookRequestModel
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.container_registry.harbor import HarborRegistry_v2
from ai.backend.manager.dto.context import ProcessorsCtx, RequestCtx
from ai.backend.manager.errors.image import (
    ContainerRegistryWebhookAuthorizationFailed,
    HarborWebhookContainerRegistryRowNotFound,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.container_registry.updaters import (
    ContainerRegistryUpdaterSpec,
)
from ai.backend.manager.services.container_registry.actions.modify_container_registry import (
    ModifyContainerRegistryAction,
)
from ai.backend.manager.types import OptionalState, TriState

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from ai.backend.manager.api.context import RootContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RegistryIdPath(BaseRequestModel):
    """Path parameter for container registry endpoints."""

    registry_id: uuid.UUID


class ContainerRegistryHandler:
    """Container registry API handler.

    Dependencies are resolved at request time via middleware parameters
    because the handler is instantiated inside ``create_app()`` before
    ``RootContext`` is available.
    """

    # ------------------------------------------------------------------
    # PATCH /container-registries/{registry_id}
    # ------------------------------------------------------------------

    async def patch(
        self,
        body: BodyParam[PatchContainerRegistryRequestModel],
        path: PathParam[RegistryIdPath],
        proc_ctx: ProcessorsCtx,
    ) -> APIResponse:
        registry_id = path.parsed.registry_id
        log.info("PATCH_CONTAINER_REGISTRY (registry:{})", registry_id)
        params = body.parsed
        processors = proc_ctx.processors

        updater_spec = ContainerRegistryUpdaterSpec(
            url=OptionalState.update(params.url) if params.url is not None else OptionalState.nop(),
            registry_name=(
                OptionalState.update(params.registry_name)
                if params.registry_name is not None
                else OptionalState.nop()
            ),
            type=(
                OptionalState.update(params.type)
                if params.type is not None
                else OptionalState.nop()
            ),
            project=(
                TriState.update(params.project) if params.project is not None else TriState.nop()
            ),
            username=(
                TriState.update(params.username) if params.username is not None else TriState.nop()
            ),
            password=(
                TriState.update(params.password) if params.password is not None else TriState.nop()
            ),
            ssl_verify=(
                TriState.update(params.ssl_verify)
                if params.ssl_verify is not None
                else TriState.nop()
            ),
            is_global=(
                TriState.update(params.is_global)
                if params.is_global is not None
                else TriState.nop()
            ),
            extra=(TriState.update(params.extra) if params.extra is not None else TriState.nop()),
            allowed_groups=(
                TriState.update(params.allowed_groups)
                if params.allowed_groups is not None
                else TriState.nop()
            ),
        )
        result = await processors.container_registry.modify_container_registry.wait_for_complete(
            ModifyContainerRegistryAction(updater=Updater(spec=updater_spec, pk_value=registry_id))
        )

        resp = PatchContainerRegistryResponseModel(
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
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # POST /container-registries/webhook/harbor
    # ------------------------------------------------------------------

    async def harbor_webhook(
        self,
        body: BodyParam[HarborWebhookRequestModel],
        ctx: RequestCtx,
    ) -> APIResponse:
        auth_header = ctx.request.headers.get("Authorization", None)
        params = body.parsed
        event_type = params.type
        resources = params.event_data.resources
        project = params.event_data.repository.namespace
        img_name = params.event_data.repository.name
        log.info("HARBOR_WEBHOOK_HANDLER (event_type:{})", event_type)

        root_ctx: RootContext = ctx.request.app["_root.context"]
        async with root_ctx.db.begin_session() as db_sess:
            for resource in resources:
                resource_url = resource.resource_url
                registry_url = resource_url.split("/")[0]

                registry_row = await _get_registry_row_matching_url(db_sess, registry_url, project)
                if not registry_row:
                    raise HarborWebhookContainerRegistryRowNotFound(
                        extra_msg=(
                            f"Harbor webhook triggered, but the matching container registry"
                            f" row not found! (registry_url: {registry_url}, project: {project})"
                        ),
                    )

                if not _is_authorized_harbor_webhook_request(auth_header, registry_row):
                    raise ContainerRegistryWebhookAuthorizationFailed(
                        extra_msg=(
                            f"Unauthorized webhook request"
                            f" (registry: {registry_row.registry_name}, project: {project})"
                        ),
                    )

                await _handle_harbor_webhook_event(
                    root_ctx, event_type, registry_row, project, img_name, resource.tag
                )

        return APIResponse.no_content(HTTPStatus.NO_CONTENT)


# ---------------------------------------------------------------------------
# Private helpers (unchanged from the original module)
# ---------------------------------------------------------------------------


async def _get_registry_row_matching_url(
    db_sess: AsyncSession, registry_url: str, project: str
) -> ContainerRegistryRow | None:
    query = sa.select(ContainerRegistryRow).where(
        (ContainerRegistryRow.type == ContainerRegistryType.HARBOR2)
        & (ContainerRegistryRow.url.like(f"%{registry_url}%"))
        & (ContainerRegistryRow.project == project)
    )
    result = await db_sess.execute(query)
    return result.scalars().one_or_none()


def _is_authorized_harbor_webhook_request(
    auth_header: str | None, registry_row: ContainerRegistryRow
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
        case "PUSH_ARTIFACT":
            await _handle_push_artifact_event(root_ctx, registry_row, project, img_name, tag)
        case _:
            log.debug(
                'Ignore harbor webhook event: "{}". Recommended to modify the webhook'
                " config to not subscribe to this event type.",
                event_type,
            )


async def _handle_push_artifact_event(
    root_ctx: RootContext,
    registry_row: ContainerRegistryRow,
    project: str,
    img_name: str,
    tag: str,
) -> None:
    scanner = HarborRegistry_v2(root_ctx.db, registry_row.registry_name, registry_row)
    await scanner.scan_single_ref(f"{project}/{img_name}:{tag}")
