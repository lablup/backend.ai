from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Self

from aiohttp import web
from click import UUID
from pydantic import ConfigDict

from ai.backend.common import redis_helper
from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    MiddlewareParam,
    QueryParam,
    api_handler,
)
from ai.backend.common.bgtask.bgtask import BgTaskInfo
from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.dto.storage.request import (
    HuggingFaceImportModelReq,
    HuggingFaceImportModelsBatchReq,
    HuggingFaceImportTaskStatusReq,
    HuggingFaceScanModelsReq,
)
from ai.backend.common.dto.storage.response import (
    BgTaskProgressData,
    HuggingFaceImportBatchResponse,
    HuggingFaceImportResponse,
    HuggingFaceScanJobStatusResponse,
    HuggingFaceScanResponse,
)
from ai.backend.common.json import load_json
from ai.backend.common.types import RedisConnectionInfo
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


class RedisStreamConnectionCtx(MiddlewareParam):
    redis_stream_conn: RedisConnectionInfo

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    async def from_request(cls, request: web.Request) -> Self:
        ctx: RootContext = request.app["ctx"]
        return cls(
            redis_stream_conn=ctx.redis_stream_conn,
        )


class HuggingFaceRegistryAPIHandler:
    _huggingface_service: HuggingFaceService

    def __init__(self, huggingface_service: HuggingFaceService) -> None:
        self._huggingface_service = huggingface_service

    @api_handler
    async def scan(
        self,
        body: BodyParam[HuggingFaceScanModelsReq],
    ) -> APIResponse:
        """
        Scan HuggingFace registry and return metadata.
        """
        await log_client_api_entry(log, "scan", body.parsed)

        try:
            models = await self._huggingface_service.scan_models(
                registry_name=body.parsed.registry_name,
                limit=body.parsed.limit,
                search=body.parsed.search,
                sort=body.parsed.order,
            )

            response = HuggingFaceScanResponse(
                models=models,
            )

            return APIResponse.build(
                status_code=HTTPStatus.OK,
                response_model=response,
            )
        except Exception as e:
            log.error("Failed to scan HuggingFace: {}", str(e))
            raise web.HTTPInternalServerError(reason=f"Scan failed: {str(e)}") from e

    @api_handler
    async def get_import_job_status(
        self,
        query: QueryParam[HuggingFaceImportTaskStatusReq],
        redis_stream_conn_ctx: RedisStreamConnectionCtx,
    ) -> APIResponse:
        """
        Get HuggingFace scan job status.
        """
        task_id = query.parsed.task_id
        redis_stream_conn = redis_stream_conn_ctx.redis_stream_conn

        await log_client_api_entry(log, "get_import_job_status", query.parsed)

        raw_task_status = await redis_helper.execute(
            redis_stream_conn, lambda r: r.get(f"bgtask.{task_id}")
        )

        task_status: BgTaskInfo
        if raw_task_status is None:
            task_status = BgTaskInfo.finished(BgtaskStatus.DONE, msg="Task already finished")
        else:
            task_status = load_json(raw_task_status)

        response = HuggingFaceScanJobStatusResponse(
            task_id=UUID(task_id),
            status=task_status.status,
            progress=BgTaskProgressData(
                current=int(task_status.current),
                total=int(task_status.total),
            ),
            message=task_status.msg,
        )

        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=response,
        )

    @api_handler
    async def import_model(
        self,
        body: BodyParam[HuggingFaceImportModelReq],
    ) -> APIResponse:
        """
        Import a HuggingFace model to storage.
        """
        await log_client_api_entry(log, "import_model", body.parsed)

        try:
            bgtask_id = await self._huggingface_service.import_model(
                registry_name=body.parsed.registry_name,
                model=body.parsed.model,
                storage_name=body.parsed.storage_name,
                bucket_name=body.parsed.bucket_name,
            )

            response = HuggingFaceImportResponse(
                task_id=bgtask_id,
            )

            return APIResponse.build(
                status_code=HTTPStatus.ACCEPTED,
                response_model=response,
            )
        except Exception as e:
            log.error("Failed to start import job: {}", str(e))
            raise web.HTTPInternalServerError(reason=f"Import failed: {str(e)}") from e

    @api_handler
    async def import_models_batch(
        self,
        body: BodyParam[HuggingFaceImportModelsBatchReq],
    ) -> APIResponse:
        """
        Import multiple HuggingFace models to storage in batch.
        """
        await log_client_api_entry(log, "import_models_batch", body.parsed)

        try:
            task_id = await self._huggingface_service.import_models_batch(
                registry_name=body.parsed.registry_name,
                models=body.parsed.models,
                storage_name=body.parsed.storage_name,
                bucket_name=body.parsed.bucket_name,
            )

            response = HuggingFaceImportBatchResponse(
                task_id=task_id,
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

    storage_service = StorageService([])

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
        )
    )
    huggingface_api_handler = HuggingFaceRegistryAPIHandler(huggingface_service=huggingface_service)

    # HuggingFace registry endpoints
    app.router.add_route("POST", "/huggingface/scan", huggingface_api_handler.scan)
    app.router.add_route(
        "GET", "/huggingface/import/{task_id}", huggingface_api_handler.get_import_job_status
    )
    app.router.add_route("POST", "/huggingface/import", huggingface_api_handler.import_model)
    app.router.add_route(
        "POST", "/huggingface/import-batch", huggingface_api_handler.import_models_batch
    )

    return app
