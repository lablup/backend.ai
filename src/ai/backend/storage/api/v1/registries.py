from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Self, override
from uuid import UUID

from aiohttp import web
from pydantic import ValidationError

from ai.backend.common.api_handlers import (
    APIResponse,
    MiddlewareParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.data.storage.registries.types import (
    HuggingFaceFileData,
    HuggingFaceModelInfo,
)
from ai.backend.common.dto.storage.request import (
    GetScanJobStatusReq,
    HuggingFaceImportModelReq,
    HuggingFaceImportModelsBatchReq,
    HuggingFaceListModelsReq,
)
from ai.backend.common.dto.storage.response import (
    HuggingFaceImportBatchResponse,
    HuggingFaceImportResponse,
    HuggingFaceScanJobStatusResponse,
    HuggingFaceScanResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.client.huggingface import (
    HuggingFaceClient,
    HuggingFaceClientArgs,
    HuggingFaceScanner,
)
from ai.backend.storage.services.artifacts.huggingface import (
    HuggingFaceService,
    HuggingFaceServiceArgs,
)
from ai.backend.storage.services.storages import StoragesService

from ...utils import log_client_api_entry

if TYPE_CHECKING:
    from ...context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RequestIntoJsonCtx(MiddlewareParam):
    json_: dict[str, Any]

    @override
    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        json = await request.json() if request.can_read_body else {}
        return cls(json_=json)


class RegistriesAPIHandler:
    _huggingface_service: HuggingFaceService

    def __init__(self, huggingface_service: HuggingFaceService) -> None:
        self._huggingface_service = huggingface_service

    @api_handler
    async def scan_huggingface(
        self,
        request_ctx: RequestIntoJsonCtx,
    ) -> APIResponse:
        """
        Scan HuggingFace registry and return metadata.
        """
        # TODO: 이거 bgtask로 돌려야 함.

        # await log_client_api_entry(log, "scan_huggingface")
        try:
            body = request_ctx.json_
            request_data = HuggingFaceListModelsReq.model_validate(body)
        except ValidationError as e:
            raise web.HTTPBadRequest(reason=f"Invalid request data: {str(e)}") from e
        except Exception as e:
            raise web.HTTPBadRequest(reason=f"Invalid JSON body: {str(e)}") from e

        try:
            models = await self._huggingface_service.list_models(
                limit=request_data.limit,
                search=request_data.search,
                sort=request_data.sort,
            )

            response = HuggingFaceScanResponse(
                models=[
                    HuggingFaceModelInfo(
                        id=model.id,
                        name=model.name,
                        author=model.author,
                        tags=model.tags,
                        pipeline_tag=model.pipeline_tag,
                        downloads=model.downloads,
                        likes=model.likes,
                        created_at=model.created_at,
                        last_modified=model.last_modified,
                        files=[
                            HuggingFaceFileData(
                                path=file.path,
                                size=file.size,
                                type=file.type,
                                download_url=file.download_url,
                                error=file.error,
                            )
                            for file in model.files
                        ],
                    )
                    for model in models
                ],
                total_count=len(models),
            )

            return APIResponse.build(
                status_code=HTTPStatus.OK,
                response_model=response,
            )
        except Exception as e:
            log.error("Failed to scan HuggingFace: {}", str(e))
            raise web.HTTPInternalServerError(reason=f"Scan failed: {str(e)}") from e

    @api_handler
    async def get_scan_job_status(
        self,
        query: QueryParam[GetScanJobStatusReq],
    ) -> APIResponse:
        """
        Get HuggingFace scan job status.
        """
        job_id = query.parsed.job_id
        if not job_id:
            raise web.HTTPBadRequest(reason="Missing job_id in query parameters")

        await log_client_api_entry(log, "get_scan_job_status", job_id)

        # TODO: Implement job status tracking
        response = HuggingFaceScanJobStatusResponse(
            job_id=UUID(job_id),
            status="completed",
            progress=100,
            message="Scan completed successfully",
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def import_huggingface_model(
        self,
        request_ctx: RequestIntoJsonCtx,
    ) -> APIResponse:
        """
        Import a HuggingFace model to storage.
        """
        # await log_client_api_entry(log, "import_huggingface_model")

        try:
            body = request_ctx.json_
            request_data = HuggingFaceImportModelReq.model_validate(body)
        except ValidationError as e:
            raise web.HTTPBadRequest(reason=f"Invalid request data: {str(e)}") from e

        try:
            job_id = await self._huggingface_service.import_model(
                model_id=request_data.model_id,
                storage_name=request_data.storage_name,
                bucket_name=request_data.bucket_name,
            )

            response = HuggingFaceImportResponse(
                job_id=job_id,
                status="started",
                model_id=request_data.model_id,
                storage_name=request_data.storage_name,
                bucket_name=request_data.bucket_name,
                message="Import job started successfully",
            )

            return APIResponse.build(
                status_code=HTTPStatus.ACCEPTED,
                response_model=response,
            )
        except Exception as e:
            log.error("Failed to start import job: {}", str(e))
            raise web.HTTPInternalServerError(reason=f"Import failed: {str(e)}") from e

    @api_handler
    async def import_huggingface_models_batch(
        self,
        request_ctx: RequestIntoJsonCtx,
    ) -> APIResponse:
        """
        Import multiple HuggingFace models to storage in batch.
        """
        # await log_client_api_entry(log, "import_huggingface_models_batch")

        # Parse request body
        try:
            body = request_ctx.json_
            request_data = HuggingFaceImportModelsBatchReq.model_validate(body)
        except ValidationError as e:
            raise web.HTTPBadRequest(reason=f"Invalid request data: {str(e)}") from e

        try:
            job_id = await self._huggingface_service.import_models_batch(
                model_ids=request_data.model_ids,
                storage_name=request_data.storage_name,
                bucket_name=request_data.bucket_name,
            )

            response = HuggingFaceImportBatchResponse(
                job_id=job_id,
                status="started",
                model_ids=request_data.model_ids,
                storage_name=request_data.storage_name,
                bucket_name=request_data.bucket_name,
                total_models=len(request_data.model_ids),
                message="Batch import job started successfully",
            )

            return APIResponse.build(
                status_code=HTTPStatus.ACCEPTED,
                response_model=response,
            )
        except Exception as e:
            log.error("Failed to start batch import job: {}", str(e))
            raise web.HTTPInternalServerError(reason=f"Batch import failed: {str(e)}") from e


def create_app(ctx: RootContext) -> web.Application:
    app = web.Application()
    app["ctx"] = ctx
    app["prefix"] = "v1/registries"

    # TODO: Must be refactored.
    storage_service = StoragesService(ctx.local_config.storages)
    huggingface_client = HuggingFaceClient(HuggingFaceClientArgs(token=None))
    scanner = HuggingFaceScanner(huggingface_client)
    huggingface_service = HuggingFaceService(
        HuggingFaceServiceArgs(
            scanner=scanner,
            background_task_manager=ctx.background_task_manager,
            storage_service=storage_service,
        )
    )
    api_handler = RegistriesAPIHandler(huggingface_service=huggingface_service)

    # HuggingFace registry endpoints
    app.router.add_route("POST", "/huggingface/scan", api_handler.scan_huggingface)
    app.router.add_route("GET", "/huggingface/scan/{job_id}", api_handler.get_scan_job_status)
    app.router.add_route("POST", "/huggingface/import", api_handler.import_huggingface_model)
    app.router.add_route(
        "POST", "/huggingface/import-batch", api_handler.import_huggingface_models_batch
    )

    return app
