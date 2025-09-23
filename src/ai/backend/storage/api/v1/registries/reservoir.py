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
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.dto.storage.request import (
    ReservoirImportModelsReq,
)
from ai.backend.common.dto.storage.response import (
    ReservoirImportModelsResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.config.unified import LegacyReservoirConfig, ReservoirConfig
from ai.backend.storage.services.artifacts.reservoir import ReservoirService, ReservoirServiceArgs

from ....utils import log_client_api_entry

if TYPE_CHECKING:
    from ....context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReservoirRegistryAPIHandler:
    _reservoir_service: ReservoirService

    def __init__(
        self,
        reservoir_service: ReservoirService,
    ) -> None:
        self._reservoir_service = reservoir_service

    @api_handler
    async def import_models(
        self,
        body: BodyParam[ReservoirImportModelsReq],
    ) -> APIResponse:
        """
        Import multiple models to storage in batch.
        """
        await log_client_api_entry(log, "import_models", None)

        task_id = await self._reservoir_service.import_models_batch(
            registry_name=body.parsed.registry_name,
            models=body.parsed.models,
            storage_name=body.parsed.storage_name,
        )

        return APIResponse.build(
            status_code=HTTPStatus.ACCEPTED,
            response_model=ReservoirImportModelsResponse(task_id=task_id),
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/registries/reservoir"

    # Get reservoir configs from new artifact_registries
    reservoir_registry_configs: list[ReservoirConfig] = [
        r.reservoir
        for r in ctx.local_config.artifact_registries.values()
        if r.registry_type == ArtifactRegistryType.RESERVOIR and r.reservoir is not None
    ]

    # Legacy registries support - add from legacy registries for backward compatibility
    for legacy_registry in ctx.local_config.registries:
        if isinstance(legacy_registry.config, LegacyReservoirConfig):
            reservoir_registry_configs.append(legacy_registry.config)

    reservoir_service = ReservoirService(
        ReservoirServiceArgs(
            background_task_manager=ctx.background_task_manager,
            event_producer=ctx.event_producer,
            storage_pool=ctx.storage_pool,
            reservoir_registry_configs=reservoir_registry_configs,
        )
    )
    reservoir_api_handler = ReservoirRegistryAPIHandler(
        reservoir_service=reservoir_service,
    )

    app.router.add_route("POST", "/import", reservoir_api_handler.import_models)

    return app
