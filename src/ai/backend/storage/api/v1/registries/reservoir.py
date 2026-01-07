from __future__ import annotations

import logging
from collections.abc import Callable
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    api_handler,
)
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.dto.storage.request import (
    ReservoirImportModelsReq,
)
from ai.backend.common.dto.storage.response import (
    ReservoirImportModelsResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.services.artifacts.reservoir import (
    ReservoirService,
    ReservoirServiceArgs,
    create_reservoir_import_pipeline,
)
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.storages.vfolder_storage import VFolderStorage
from ai.backend.storage.utils import log_client_api_entry
from ai.backend.storage.volumes.pool import VolumePool

if TYPE_CHECKING:
    from ai.backend.storage.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReservoirRegistryAPIHandler:
    _reservoir_service: ReservoirService
    _volume_pool: VolumePool
    _storage_pool: StoragePool

    def __init__(
        self,
        reservoir_service: ReservoirService,
        volume_pool: VolumePool,
        storage_pool: StoragePool,
    ) -> None:
        self._reservoir_service = reservoir_service
        self._volume_pool = volume_pool
        self._storage_pool = storage_pool

    @api_handler
    async def import_models(
        self,
        body: BodyParam[ReservoirImportModelsReq],
    ) -> APIResponse:
        """
        Import multiple models to storage in batch.
        """
        await log_client_api_entry(log, "import_models", None)

        storage_step_mappings = body.parsed.storage_step_mappings
        vfolder_storage_name: str | None = None
        cleanup_callback: Callable[[], None] | None = None

        # If vfid is provided, create VFolderStorage and register it
        if body.parsed.vfid is not None:
            vfid = body.parsed.vfid
            request_id = current_request_id()
            # Get the volume name from storage_step_mappings
            # When vfid is provided, all steps should use the same volume (vfolder's host)
            volume_names = set(storage_step_mappings.values())
            if len(volume_names) != 1:
                log.warning(
                    f"Multiple volume names in storage_step_mappings with vfid: {volume_names}"
                )
            volume_name = next(iter(volume_names))

            # Create VFolderStorage
            async with self._volume_pool.get_volume_by_name(volume_name) as volume:
                vfolder_storage_name = f"vfolder_{request_id}"
                vfolder_storage = VFolderStorage(
                    name=vfolder_storage_name,
                    volume=volume,
                    vfid=vfid,
                )

                # Register to storage pool
                self._storage_pool.add_storage(vfolder_storage_name, vfolder_storage)

                log.info(
                    f"Created VFolderStorage: name={vfolder_storage_name}, vfid={vfid}, "
                    f"volume={volume_name}"
                )

            # Override storage_step_mappings to use VFolderStorage
            storage_step_mappings = dict.fromkeys(
                storage_step_mappings.keys(), vfolder_storage_name
            )

            # Create cleanup callback to remove VFolderStorage after task completion
            def _cleanup() -> None:
                if vfolder_storage_name is not None:
                    self._storage_pool.remove_storage(vfolder_storage_name)
                    log.info(f"Removed VFolderStorage: name={vfolder_storage_name}")

            cleanup_callback = _cleanup

        # Create import pipeline based on storage step mappings
        pipeline = create_reservoir_import_pipeline(
            storage_pool=self._reservoir_service._storage_pool,
            registry_configs=self._reservoir_service._reservoir_registry_configs,
            storage_step_mappings=storage_step_mappings,
            transfer_manager=self._reservoir_service._transfer_manager,
            artifact_verifier_ctx=self._reservoir_service._artifact_verifier_ctx,
            event_producer=self._reservoir_service._event_producer,
            manager_client_pool=self._reservoir_service._manager_client_pool,
            redis_client=self._reservoir_service._redis_client,
        )

        task_id = await self._reservoir_service.import_models_batch(
            registry_name=body.parsed.registry_name,
            models=body.parsed.models,
            storage_step_mappings=storage_step_mappings,
            pipeline=pipeline,
            artifact_revision_ids=[UUID(rev_id) for rev_id in body.parsed.artifact_revision_ids],
            on_complete=cleanup_callback,
        )

        return APIResponse.build(
            status_code=HTTPStatus.ACCEPTED,
            response_model=ReservoirImportModelsResponse(task_id=task_id),
        )


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/registries/reservoir"

    reservoir_service = ReservoirService(
        ReservoirServiceArgs(
            background_task_manager=ctx.background_task_manager,
            event_producer=ctx.event_producer,
            storage_pool=ctx.storage_pool,
            reservoir_registry_configs=ctx.manager_client_pool.registry_configs,
            artifact_verifier_ctx=ctx.artifact_verifier_ctx,
            manager_client_pool=ctx.manager_client_pool,
            redis_client=ctx.valkey_artifact_client,
        )
    )
    reservoir_api_handler = ReservoirRegistryAPIHandler(
        reservoir_service=reservoir_service,
        volume_pool=ctx.volume_pool,
        storage_pool=ctx.storage_pool,
    )

    app.router.add_route("POST", "/import", reservoir_api_handler.import_models)

    return app
