from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    api_handler,
)
from ai.backend.common.dto.storage.request import (
    HuggingFaceImportModelsReq,
    HuggingFaceScanModelsReq,
)
from ai.backend.common.dto.storage.response import (
    HuggingFaceImportModelsResponse,
    HuggingFaceScanModelsResponse,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.services.artifacts.huggingface import (
    HuggingFaceService,
    HuggingFaceServiceArgs,
)
from ai.backend.storage.services.storages import StorageService

from ...utils import log_client_api_entry

if TYPE_CHECKING:
    from ...context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HuggingFaceRegistryAPIHandler:
    _huggingface_service: HuggingFaceService
    _event_producer: EventProducer

    def __init__(
        self, huggingface_service: HuggingFaceService, event_producer: EventProducer
    ) -> None:
        self._huggingface_service = huggingface_service
        self._event_producer = event_producer

    @api_handler
    async def scan_models(
        self,
        body: BodyParam[HuggingFaceScanModelsReq],
    ) -> APIResponse:
        """
        Scan HuggingFace registry and return metadata.
        """
        await log_client_api_entry(log, "scan", body.parsed)

        models = await self._huggingface_service.scan_models(
            registry_name=body.parsed.registry_name,
            limit=body.parsed.limit,
            search=body.parsed.search,
            sort=body.parsed.order,
        )

        response = HuggingFaceScanModelsResponse(
            models=models,
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def import_models(
        self,
        body: BodyParam[HuggingFaceImportModelsReq],
    ) -> APIResponse:
        """
        Import multiple HuggingFace models to storage in batch.
        """
        await log_client_api_entry(log, "import_models_batch", body.parsed)

        task_id = await self._huggingface_service.import_models_batch(
            registry_name=body.parsed.registry_name,
            models=body.parsed.models,
            storage_name=body.parsed.storage_name,
            bucket_name=body.parsed.bucket_name,
        )

        response = HuggingFaceImportModelsResponse(
            task_id=task_id,
        )

        return APIResponse.build(
            status_code=HTTPStatus.ACCEPTED,
            response_model=response,
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/registries"

    storage_service = StorageService(storage_configs=ctx.local_config.storages)

    huggingface_registry_configs = dict(
        (r.name, r.config)
        for r in ctx.local_config.registries
        if r.config.registry_type == "huggingface"
    )

    huggingface_service = HuggingFaceService(
        HuggingFaceServiceArgs(
            background_task_manager=ctx.background_task_manager,
            storage_service=storage_service,
            registry_configs=huggingface_registry_configs,
            event_producer=ctx.event_producer,
        )
    )
    huggingface_api_handler = HuggingFaceRegistryAPIHandler(
        huggingface_service=huggingface_service, event_producer=ctx.event_producer
    )

    # HuggingFace registry endpoints
    app.router.add_route("POST", "/huggingface/scan", huggingface_api_handler.scan_models)
    app.router.add_route("POST", "/huggingface/import", huggingface_api_handler.import_models)

    return app
