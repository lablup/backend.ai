"""Container registry handler using the new ApiHandler pattern.

All handlers use typed parameters (``BodyParam``, ``PathParam``,
``QueryParam``, ``RequestCtx``) that are automatically extracted by
``_wrap_api_handler``, and responses are returned as ``APIResponse``
objects.
"""

from __future__ import annotations

import logging
import uuid
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRequestModel,
    BodyParam,
    PathParam,
    QueryParam,
)
from ai.backend.common.container_registry import (
    ContainerRegistryModel,
    CreateContainerRegistryRequestModel,
    ImageOperationRequestModel,
    ListContainerRegistriesResponseModel,
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.dto.manager.registry.request import HarborWebhookRequestModel
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx
from ai.backend.manager.models.container_registry.creators import ContainerRegistryCreator
from ai.backend.manager.models.container_registry.purgers import ContainerRegistryPurger
from ai.backend.manager.models.container_registry.updaters import ContainerRegistryUpdater
from ai.backend.manager.services.container_registry.actions.clear_images import ClearImagesAction
from ai.backend.manager.services.container_registry.actions.create_container_registry import (
    CreateContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.delete_container_registry import (
    DeleteContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.actions.handle_harbor_webhook import (
    HandleHarborWebhookAction,
    HarborWebhookResourceInput,
)
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import RescanImagesAction
from ai.backend.manager.services.container_registry.actions.update_container_registry import (
    UpdateContainerRegistryAction,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.types import OptionalState, TriState

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RegistryIdPath(BaseRequestModel):
    """Path parameter for container registry endpoints."""

    registry_id: uuid.UUID


class LoadContainerRegistriesQueryModel(BaseRequestModel):
    """Query parameters for load endpoint."""

    registry: str
    project: str | None = None


class ContainerRegistryHandler:
    """Container registry API handler.

    Dependencies are injected via constructor at registrar time.
    """

    def __init__(self, *, container_registry: ContainerRegistryProcessors) -> None:
        self._container_registry = container_registry

    # ------------------------------------------------------------------
    # POST /container-registries
    # ------------------------------------------------------------------

    async def create(
        self,
        body: BodyParam[CreateContainerRegistryRequestModel],
    ) -> APIResponse:
        params = body.parsed

        creator = ContainerRegistryCreator(
            url=params.url,
            registry_name=params.registry_name,
            type=params.type,
            project=params.project,
            username=params.username,
            password=params.password,
            ssl_verify=params.ssl_verify,
            is_global=params.is_global,
            extra=params.extra,
            allowed_groups=params.allowed_groups,
        )
        result = await self._container_registry.create_container_registry.run(
            CreateContainerRegistryAction(creator=creator)
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
        return APIResponse.build(HTTPStatus.CREATED, resp)

    # ------------------------------------------------------------------
    # DELETE /container-registries/{registry_id}
    # ------------------------------------------------------------------

    async def delete(
        self,
        path: PathParam[RegistryIdPath],
    ) -> APIResponse:
        registry_id = path.parsed.registry_id

        await self._container_registry.delete_container_registry.run(
            DeleteContainerRegistryAction(
                purger=ContainerRegistryPurger(registry_id=ContainerRegistryID(registry_id))
            )
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # GET /container-registries
    # ------------------------------------------------------------------

    async def list_all(self) -> APIResponse:
        result = await self._container_registry.load_all_container_registries.run(
            LoadAllContainerRegistriesAction()
        )

        resp = ListContainerRegistriesResponseModel(
            items=[
                ContainerRegistryModel(
                    id=reg.id,
                    url=reg.url,
                    registry_name=reg.registry_name,
                    type=reg.type,
                    project=reg.project,
                    username=reg.username,
                    password=reg.password,
                    ssl_verify=reg.ssl_verify,
                    is_global=reg.is_global,
                    extra=reg.extra,
                )
                for reg in result.registries
            ]
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # GET /container-registries/load
    # ------------------------------------------------------------------

    async def load(
        self,
        query: QueryParam[LoadContainerRegistriesQueryModel],
    ) -> APIResponse:
        params = query.parsed

        result = await self._container_registry.load_container_registries.run(
            LoadContainerRegistriesAction(registry=params.registry, project=params.project)
        )

        resp = ListContainerRegistriesResponseModel(
            items=[
                ContainerRegistryModel(
                    id=reg.id,
                    url=reg.url,
                    registry_name=reg.registry_name,
                    type=reg.type,
                    project=reg.project,
                    username=reg.username,
                    password=reg.password,
                    ssl_verify=reg.ssl_verify,
                    is_global=reg.is_global,
                    extra=reg.extra,
                )
                for reg in result.registries
            ]
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # PATCH /container-registries/{registry_id}
    # ------------------------------------------------------------------

    async def patch(
        self,
        body: BodyParam[PatchContainerRegistryRequestModel],
        path: PathParam[RegistryIdPath],
    ) -> APIResponse:
        registry_id = path.parsed.registry_id
        params = body.parsed

        updater = ContainerRegistryUpdater(
            registry_id=ContainerRegistryID(registry_id),
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
        result = await self._container_registry.update_container_registry.run(
            UpdateContainerRegistryAction(updater=updater)
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
    # POST /container-registries/rescan
    # ------------------------------------------------------------------

    async def rescan_images(
        self,
        body: BodyParam[ImageOperationRequestModel],
    ) -> APIResponse:
        params = body.parsed

        await self._container_registry.rescan_images.run(
            RescanImagesAction(
                registry=params.registry,
                project=params.project,
                progress_reporter=None,
            )
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # POST /container-registries/clear
    # ------------------------------------------------------------------

    async def clear_images(
        self,
        body: BodyParam[ImageOperationRequestModel],
    ) -> APIResponse:
        params = body.parsed

        await self._container_registry.clear_images.run(
            ClearImagesAction(registry=params.registry, project=params.project)
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

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
        project = params.event_data.repository.namespace
        img_name = params.event_data.repository.name

        resources = [
            HarborWebhookResourceInput(
                resource_url=r.resource_url,
                tag=r.tag,
            )
            for r in params.event_data.resources
        ]

        action = HandleHarborWebhookAction(
            event_type=event_type,
            resources=resources,
            project=project,
            img_name=img_name,
            auth_header=auth_header,
        )
        await self._container_registry.handle_harbor_webhook.run(action)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)
