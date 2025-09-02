"""HuggingFace model scanner implementation for Backend.AI storage."""

import asyncio
import logging
import mimetypes
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Optional

import aioboto3

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import ModelImportDoneEvent
from ai.backend.common.types import DispatchResult
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.client.s3 import S3Client
from ai.backend.storage.config.unified import (
    ObjectStorageConfig,
    ReservoirConfig,
)
from ai.backend.storage.exception import (
    HuggingFaceModelNotFoundError,
    ReservoirStorageConfigInvalidError,
    StorageBucketNotFoundError,
    StorageNotFoundError,
)
from ai.backend.storage.services.storages import StorageService
from ai.backend.storage.types import BucketCopyOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ReservoirServiceArgs:
    background_task_manager: BackgroundTaskManager
    storage_service: StorageService
    event_producer: EventProducer
    storage_configs: list[ObjectStorageConfig]
    reservoir_registry_configs: list[ReservoirConfig]


class ReservoirService:
    """Service for Reservoir model operations"""

    _storages_service: StorageService
    _background_task_manager: BackgroundTaskManager
    _event_producer: EventProducer
    _storage_configs: dict[str, ObjectStorageConfig]
    _reservoir_registry_configs: list[ReservoirConfig]

    def __init__(self, args: ReservoirServiceArgs):
        self._storages_service = args.storage_service
        self._background_task_manager = args.background_task_manager
        self._event_producer = args.event_producer
        self._storage_configs = {cfg.name: cfg for cfg in args.storage_configs}
        self._reservoir_registry_configs = args.reservoir_registry_configs

    def _get_s3_client(self, storage_name: str, bucket_name: str) -> S3Client:
        storage_config = self._storage_configs.get(storage_name)
        if not storage_config:
            raise StorageNotFoundError(
                f"No storage configuration found for storage: {storage_name}"
            )

        if bucket_name not in storage_config.buckets:
            raise StorageBucketNotFoundError(
                f"Bucket '{bucket_name}' not found in storage '{storage_name}'"
            )

        return S3Client(
            bucket_name=bucket_name,
            endpoint_url=storage_config.endpoint,
            region_name=storage_config.region,
            aws_access_key_id=storage_config.access_key,
            aws_secret_access_key=storage_config.secret_key,
        )

    async def _list_all_keys_and_sizes(
        self,
        *,
        endpoint_url: str,
        access_key: Optional[str],
        secret_key: Optional[str],
        region: Optional[str],
        bucket: str,
        prefix: Optional[str] = None,  # ✅ 추가됨
    ) -> tuple[list[str], dict[str, int], int]:
        """
        List all non-marker object keys in the given bucket (optionally under a prefix).

        Returns:
            keys: list of object keys
            size_map: mapping from key -> object size
            total_bytes: total sum of all object sizes
        """
        session = aioboto3.Session()
        keys: list[str] = []
        size_map: dict[str, int] = {}
        total = 0

        log.trace("[list] start bucket={} prefix={} endpoint={}", bucket, prefix, endpoint_url)

        async with session.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        ) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            kwargs = {"Bucket": bucket}
            if prefix:
                kwargs["Prefix"] = prefix

            async for page in paginator.paginate(**kwargs):
                for obj in page.get("Contents", []) or []:
                    key = obj["Key"]
                    if key.endswith("/"):  # directory marker skip
                        continue
                    size = int(obj.get("Size", 0))
                    keys.append(key)
                    size_map[key] = size
                    total += size

        log.trace("[list] done keys={} total_bytes={}", len(keys), total)
        return keys, size_map, total

    async def stream_bucket_to_bucket(
        self,
        src: ReservoirConfig,
        storage_name: str,
        bucket_name: str,
        options: BucketCopyOptions,
        progress_reporter: ProgressReporter,
        key_prefix: Optional[str] = None,
    ) -> int:
        """
        Stream-copy objects from the source bucket (optionally under key_prefix)
        to the destination bucket.
        Returns the number of copied objects.
        """
        dst_client = self._get_s3_client(storage_name, bucket_name)
        download_chunk_size = self._storage_configs[storage_name].remote_storage_download_chunk_size

        # List all objects under prefix
        target_keys, size_map, total_bytes = await self._list_all_keys_and_sizes(
            endpoint_url=src.endpoint,
            access_key=src.object_storage_access_key,
            secret_key=src.object_storage_secret_key,
            region=src.object_storage_region,
            bucket=bucket_name,
            prefix=key_prefix,
        )

        if not target_keys:
            log.trace("[stream_bucket_to_bucket] no objects to copy; nothing to do")
            return 0

        log.trace(
            "[stream_bucket_to_bucket] start src_endpoint={} src_bucket={} src_prefix={} "
            "dst_storage={} dst_bucket={} objects={} total_bytes={} concurrency={}",
            src.endpoint,
            bucket_name,
            key_prefix,
            storage_name,
            bucket_name,
            len(target_keys),
            total_bytes,
            options.concurrency,
        )

        copied = 0
        sem = asyncio.Semaphore(options.concurrency)

        src_s3_client = S3Client(
            bucket_name=bucket_name,
            endpoint_url=src.endpoint,
            region_name=src.object_storage_region,
            aws_access_key_id=src.object_storage_access_key,
            aws_secret_access_key=src.object_storage_secret_key,
        )

        async def _copy_single_object(key: str) -> None:
            async with sem:
                size = size_map.get(key, -1)
                log.trace("[stream_bucket_to_bucket] begin key={} size={}", key, size)

                async def _data_stream() -> AsyncIterator[bytes]:
                    sent = 0
                    next_mark = options.progress_log_interval_bytes
                    async for chunk in src_s3_client.download_stream(
                        key, chunk_size=download_chunk_size
                    ):
                        sent += len(chunk)
                        if next_mark and sent >= next_mark:
                            log.trace(
                                "[stream_bucket_to_bucket] progress key={} sent={}/{}",
                                key,
                                sent,
                                size,
                            )
                            next_mark += options.progress_log_interval_bytes
                        yield chunk

                # Content-Type
                object_meta = await src_s3_client.get_object_meta(key)
                ctype = (
                    (object_meta.content_type if object_meta else None)
                    or mimetypes.guess_type(key)[0]
                    or "application/octet-stream"
                )

                part_size = self._storage_configs[storage_name].upload_chunk_size
                await dst_client.upload_stream(
                    _data_stream(),
                    key,
                    content_type=ctype,
                    part_size=part_size,
                )

                log.trace("[stream_bucket_to_bucket] done key={} bytes={}", key, size)

        await asyncio.gather(*(_copy_single_object(k) for k in target_keys))
        copied = len(target_keys)

        log.trace(
            "[stream_bucket_to_bucket] all done objects={} total_bytes={}", copied, total_bytes
        )
        return copied

    async def import_model(
        self,
        registry_name: str,
        model: ModelTarget,
        storage_name: str,
        bucket_name: str,
        reporter: ProgressReporter,
    ) -> None:
        """ """
        if len(self._reservoir_registry_configs) == 0:
            raise ReservoirStorageConfigInvalidError("No reservoir registry configuration found.")

        reservoir_config = self._reservoir_registry_configs[0]
        prefix_key = f"{model.model_id}/{model.revision}"

        print("prefix_key!", prefix_key)

        await self.stream_bucket_to_bucket(
            src=reservoir_config,
            storage_name=storage_name,
            bucket_name=bucket_name,
            options=BucketCopyOptions(
                concurrency=16,
                progress_log_interval_bytes=0,  # disabled
            ),
            progress_reporter=reporter,
            key_prefix=prefix_key,
        )

        await self._event_producer.anycast_event(
            ModelImportDoneEvent(
                model_id=model.model_id,
                revision=model.revision,
                registry_name=registry_name,
                registry_type=ArtifactRegistryType.RESERVOIR,
                total_size=-1,
            )
        )

    async def import_models_batch(
        self,
        registry_name: str,
        models: list[ModelTarget],
        storage_name: str,
        bucket_name: str,
    ):
        async def _import_models_batch(reporter: ProgressReporter) -> DispatchResult:
            model_count = len(models)
            if not model_count:
                log.warning("No models to import")
                return DispatchResult.error("No models provided for batch import")

            reporter.total_progress = model_count

            log.info(
                f"Starting batch model import: model_count={model_count}, "
                f"(storage_name={storage_name}, bucket_name={bucket_name})"
            )

            try:
                successful_models = 0
                failed_models = 0
                errors = []

                # Process each model sequentially to avoid overwhelming the system
                # In a production system, this could be enhanced with parallel processing
                # and proper job queue management
                for idx, model in enumerate(models, 1):
                    model_id = model.model_id
                    try:
                        log.info(
                            f"Processing model in batch: model_id={model_id}, progress={idx}/{model_count}"
                        )

                        # TODO: Batch import logic can be optimized further
                        await self.import_model(
                            registry_name,
                            model=model,
                            storage_name=storage_name,
                            bucket_name=bucket_name,
                            reporter=reporter,
                        )

                        successful_models += 1
                        log.info(
                            f"Successfully imported model in batch: model_id={model_id}, progress={idx}/{model_count}"
                        )

                    except HuggingFaceModelNotFoundError as e:
                        failed_models += 1
                        log.error(
                            f"Model not found in batch import: model_id={model_id}, progress={idx}/{model_count}"
                        )
                        errors.append(str(e))

                    except Exception as e:
                        failed_models += 1
                        log.error(
                            f"Failed to import model in batch: {str(e)}, model_id={model_id}, progress={idx}/{model_count}"
                        )
                        errors.append(str(e))
                    finally:
                        await reporter.update(
                            1,
                            message=f"Processed model: {model_id} (progress: {idx}/{model_count})",
                        )

                log.info(
                    f"Batch model import completed: total_models={model_count}, "
                    f"successful_models={successful_models}, failed_models={failed_models}"
                )

                if failed_models > 0:
                    log.warning(
                        f"Some models failed to import in batch: failed_count={failed_models}"
                    )
                    return DispatchResult.partial_success(None, errors=errors)
            except Exception as e:
                log.error(f"Batch model import failed: {str(e)}")
                return DispatchResult.error(f"Batch import failed: {str(e)}")

            return DispatchResult.success(None)

        bgtask_id = await self._background_task_manager.start(_import_models_batch)
        return bgtask_id
