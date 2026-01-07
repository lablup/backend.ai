from __future__ import annotations

import logging
from collections.abc import Callable
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import unquote

from aiohttp import web

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.common.dto.storage.request import (
    HuggingFaceGetCommitHashReqPathParam,
    HuggingFaceGetCommitHashReqQueryParam,
    HuggingFaceImportModelsReq,
    HuggingFaceRetrieveModelReqPathParam,
    HuggingFaceRetrieveModelReqQueryParam,
    HuggingFaceRetrieveModelsReq,
    HuggingFaceScanModelsReq,
)
from ai.backend.common.dto.storage.response import (
    HuggingFaceGetCommitHashResponse,
    HuggingFaceImportModelsResponse,
    HuggingFaceRetrieveModelResponse,
    HuggingFaceRetrieveModelsResponse,
    HuggingFaceScanModelsResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.api.types import VFolderStorageSetupResult
from ai.backend.storage.config.unified import (
    HuggingfaceConfig,
    LegacyHuggingfaceConfig,
)
from ai.backend.storage.services.artifacts.huggingface import (
    HuggingFaceService,
    HuggingFaceServiceArgs,
    create_huggingface_import_pipeline,
)
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.storages.vfolder_storage import VFolderStorage
from ai.backend.storage.utils import log_client_api_entry
from ai.backend.storage.volumes.pool import VolumePool

if TYPE_CHECKING:
    from ai.backend.common.types import VFolderID
    from ai.backend.storage.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HuggingFaceRegistryAPIHandler:
    _huggingface_service: HuggingFaceService
    _volume_pool: VolumePool
    _storage_pool: StoragePool

    def __init__(
        self,
        huggingface_service: HuggingFaceService,
        volume_pool: VolumePool,
        storage_pool: StoragePool,
    ) -> None:
        self._huggingface_service = huggingface_service
        self._volume_pool = volume_pool
        self._storage_pool = storage_pool

    async def _setup_vfolder_storage(
        self,
        vfid: VFolderID,
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
    ) -> VFolderStorageSetupResult:
        """Setup VFolderStorage for import operations.

        Creates a temporary VFolderStorage, registers it to the storage pool,
        and returns updated storage_step_mappings along with a cleanup callback.

        Args:
            vfid: VFolder ID to create storage for
            storage_step_mappings: Original storage step mappings

        Returns:
            VFolderStorageSetupResult with updated mappings and cleanup callback
        """
        request_id = current_request_id()
        # Get the volume name from storage_step_mappings
        # When vfid is provided, all steps should use the same volume (vfolder's host)
        volume_names = set(storage_step_mappings.values())
        if len(volume_names) != 1:
            log.warning(f"Multiple volume names in storage_step_mappings with vfid: {volume_names}")
        volume_name = next(iter(volume_names))

        # Create VFolderStorage
        async with self._volume_pool.get_volume_by_name(volume_name) as volume:
            vfolder_storage_name = f"vfolder_storage_{request_id}"
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
        updated_mappings = dict.fromkeys(storage_step_mappings.keys(), vfolder_storage_name)

        # Create cleanup callback to remove VFolderStorage after task completion
        def _cleanup() -> None:
            self._storage_pool.remove_storage(vfolder_storage_name)
            log.info(f"Removed VFolderStorage: name={vfolder_storage_name}")

        return VFolderStorageSetupResult(
            storage_step_mappings=updated_mappings,
            cleanup_callback=_cleanup,
        )

    @api_handler
    async def scan_models(
        self,
        body: BodyParam[HuggingFaceScanModelsReq],
    ) -> APIResponse:
        """
        Scan HuggingFace registry and return metadata.
        """
        await log_client_api_entry(log, "scan_models", body.parsed)

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
    async def retrieve_model(
        self,
        path: PathParam[HuggingFaceRetrieveModelReqPathParam],
        query: QueryParam[HuggingFaceRetrieveModelReqQueryParam],
    ) -> APIResponse:
        """
        Retrieve HuggingFace registry model data.
        """
        await log_client_api_entry(log, "retrieve_model", path.parsed.model_id)

        model_id = unquote(path.parsed.model_id)
        model_data = await self._huggingface_service.retrieve_model(
            registry_name=query.parsed.registry_name,
            model=ModelTarget(
                model_id=model_id,
                revision=query.parsed.revision,
            ),
        )

        response = HuggingFaceRetrieveModelResponse(
            model=model_data,
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def retrieve_models(
        self,
        body: BodyParam[HuggingFaceRetrieveModelsReq],
    ) -> APIResponse:
        """
        Retrieve HuggingFace registry model data.
        """
        await log_client_api_entry(log, "retrieve_models", body.parsed)

        model_datas = await self._huggingface_service.retrieve_models(
            registry_name=body.parsed.registry_name,
            models=body.parsed.models,
        )

        response = HuggingFaceRetrieveModelsResponse(
            models=model_datas,
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def get_commit_hash(
        self,
        path: PathParam[HuggingFaceGetCommitHashReqPathParam],
        query: QueryParam[HuggingFaceGetCommitHashReqQueryParam],
    ) -> APIResponse:
        """
        Get the commit hash for a specific HuggingFace model revision.
        """
        await log_client_api_entry(log, "get_commit_hash", path.parsed.model_id)

        model_id = unquote(path.parsed.model_id)
        commit_hash = await self._huggingface_service.get_model_commit_hash(
            registry_name=query.parsed.registry_name,
            model=ModelTarget(
                model_id=model_id,
                revision=query.parsed.revision,
            ),
        )

        response = HuggingFaceGetCommitHashResponse(
            commit_hash=commit_hash,
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
        await log_client_api_entry(log, "import_models", body.parsed)

        storage_step_mappings = body.parsed.storage_step_mappings
        cleanup_callback: Callable[[], None] | None = None

        # If vfid is provided, create VFolderStorage and register it
        if body.parsed.vfid is not None:
            setup_result = await self._setup_vfolder_storage(
                body.parsed.vfid, storage_step_mappings
            )
            storage_step_mappings = setup_result.storage_step_mappings
            cleanup_callback = setup_result.cleanup_callback

        # Create import pipeline based on storage step mappings
        pipeline = create_huggingface_import_pipeline(
            registry_configs=self._huggingface_service._registry_configs,
            transfer_manager=self._huggingface_service._transfer_manager,
            storage_step_mappings=storage_step_mappings,
            artifact_verifier_ctx=self._huggingface_service._artifact_verifier_ctx,
            event_producer=self._huggingface_service._event_producer,
            redis_client=self._huggingface_service._redis_client,
        )

        task_id = await self._huggingface_service.import_models_batch(
            registry_name=body.parsed.registry_name,
            models=body.parsed.models,
            storage_step_mappings=storage_step_mappings,
            pipeline=pipeline,
            on_complete=cleanup_callback,
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
    app["prefix"] = "v1/registries/huggingface"

    # Get huggingface configs from new artifact_registries
    huggingface_registry_configs: dict[str, HuggingfaceConfig] = {
        name: r.huggingface
        for name, r in ctx.local_config.artifact_registries.items()
        if r.registry_type == ArtifactRegistryType.HUGGINGFACE and r.huggingface is not None
    }

    # Legacy registry configs support - add from legacy registries for backward compatibility
    for legacy_registry in ctx.local_config.registries:
        if isinstance(legacy_registry.config, LegacyHuggingfaceConfig):
            huggingface_registry_configs[legacy_registry.name] = legacy_registry.config

    huggingface_service = HuggingFaceService(
        HuggingFaceServiceArgs(
            background_task_manager=ctx.background_task_manager,
            storage_pool=ctx.storage_pool,
            registry_configs=huggingface_registry_configs,
            event_producer=ctx.event_producer,
            artifact_verifier_ctx=ctx.artifact_verifier_ctx,
            redis_client=ctx.valkey_artifact_client,
        )
    )
    huggingface_api_handler = HuggingFaceRegistryAPIHandler(
        huggingface_service=huggingface_service,
        volume_pool=ctx.volume_pool,
        storage_pool=ctx.storage_pool,
    )

    app.router.add_route("POST", "/scan", huggingface_api_handler.scan_models)
    app.router.add_route("POST", "/import", huggingface_api_handler.import_models)

    app.router.add_route("GET", "/model/{model_id}", huggingface_api_handler.retrieve_model)
    app.router.add_route(
        "GET", "/model/{model_id}/commit-hash", huggingface_api_handler.get_commit_hash
    )
    app.router.add_route("POST", "/models/batch", huggingface_api_handler.retrieve_models)
    return app
