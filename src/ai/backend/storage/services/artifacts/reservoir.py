import asyncio
import logging
import mimetypes
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import ModelImportDoneEvent
from ai.backend.common.types import DispatchResult, StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.client.s3 import S3Client
from ai.backend.storage.config.unified import (
    ReservoirConfig,
)
from ai.backend.storage.exception import (
    ArtifactRevisionEmptyError,
    ArtifactStorageEmptyError,
    ObjectStorageBucketNotFoundError,
    ReservoirStorageConfigInvalidError,
    StorageNotFoundError,
)
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.types import BucketCopyOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ReservoirServiceArgs:
    background_task_manager: BackgroundTaskManager
    event_producer: EventProducer
    storage_pool: StoragePool
    reservoir_registry_configs: list[ReservoirConfig]


class ReservoirFileDownloadStreamReader(StreamReader):
    _src_s3_client: S3Client
    _key: str
    _size: int
    _options: BucketCopyOptions
    _download_chunk_size: int
    _content_type: Optional[str]

    def __init__(
        self,
        src_s3_client: S3Client,
        key: str,
        size: int,
        options: BucketCopyOptions,
        download_chunk_size: int,
        content_type: Optional[str],
    ):
        self._src_s3_client = src_s3_client
        self._key = key
        self._size = size
        self._options = options
        self._download_chunk_size = download_chunk_size
        self._content_type = content_type

    @override
    async def read(self) -> AsyncIterator[bytes]:
        sent = 0
        next_mark = self._options.progress_log_interval_bytes
        download_stream = self._src_s3_client.download_stream(
            self._key, chunk_size=self._download_chunk_size
        )
        async for chunk in download_stream.read():
            sent += len(chunk)
            if next_mark and sent >= next_mark:
                log.trace(
                    "[stream_bucket_to_bucket] progress key={} sent={}/{}",
                    self._key,
                    sent,
                    self._size,
                )
                next_mark += self._options.progress_log_interval_bytes
            yield chunk

    @override
    def content_type(self) -> Optional[str]:
        return self._content_type


class ReservoirService:
    """Service for Reservoir model operations"""

    _background_task_manager: BackgroundTaskManager
    _event_producer: EventProducer
    _reservoir_registry_configs: list[ReservoirConfig]
    _storage_pool: StoragePool

    def __init__(self, args: ReservoirServiceArgs):
        self._background_task_manager = args.background_task_manager
        self._event_producer = args.event_producer
        self._reservoir_registry_configs = args.reservoir_registry_configs
        self._storage_pool = args.storage_pool

    def _get_s3_client(self, storage_name: str) -> tuple[S3Client, str]:
        if not self._storage_pool:
            raise StorageNotFoundError("Storage pool not configured")

        # Get storage from pool and verify it's ObjectStorage type
        try:
            storage = self._storage_pool.get_storage(storage_name)
        except KeyError:
            raise StorageNotFoundError(f"Storage '{storage_name}' not found in pool")

        if not isinstance(storage, ObjectStorage):
            raise StorageNotFoundError(
                f"Storage '{storage_name}' is not an ObjectStorage type. "
                f"Reservoir import requires ObjectStorage for S3 operations."
            )

        # Use the configured bucket from ObjectStorage
        bucket_name = storage._bucket
        if not bucket_name:
            raise ObjectStorageBucketNotFoundError(
                f"No bucket configured for storage '{storage_name}'"
            )

        # Create S3Client from ObjectStorage configuration
        s3_client = S3Client(
            bucket_name=bucket_name,
            endpoint_url=storage._endpoint,
            region_name=storage._region,
            aws_access_key_id=storage._access_key,
            aws_secret_access_key=storage._secret_key,
        )
        return s3_client, bucket_name

    async def _list_all_keys_and_sizes(
        self,
        *,
        s3_client: S3Client,
        prefix: Optional[str] = None,
    ) -> tuple[list[str], dict[str, int], int]:
        """
        List all non-marker object keys in the given bucket (optionally under a prefix).

        Returns:
            keys: list of object keys
            size_map: mapping from key -> object size
            total_bytes: total sum of all object sizes
        """
        keys: list[str] = []
        size_map: dict[str, int] = {}
        total = 0

        log.trace(
            "[list] start bucket={} prefix={} endpoint={}",
            s3_client.bucket_name,
            prefix,
            s3_client.endpoint_url,
        )

        async with s3_client.session.client(
            "s3",
            endpoint_url=s3_client.endpoint_url,
            region_name=s3_client.region_name,
            aws_access_key_id=s3_client.aws_access_key_id,
            aws_secret_access_key=s3_client.aws_secret_access_key,
        ) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            kwargs = {"Bucket": s3_client.bucket_name}
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

    async def _stream_bucket_to_bucket(
        self,
        source_cfg: ReservoirConfig,
        storage_name: str,
        options: BucketCopyOptions,
        progress_reporter: ProgressReporter,
        key_prefix: Optional[str] = None,
    ) -> int:
        """
        Stream-copy objects from the source bucket (optionally under key_prefix)
        to the destination bucket.

        Returns:
            the total number of bytes copied.
        """
        dst_client, bucket_name = self._get_s3_client(storage_name)

        # Get storage from pool to access configuration
        try:
            storage = self._storage_pool.get_storage(storage_name)
        except KeyError:
            raise StorageNotFoundError(f"Storage '{storage_name}' not found in pool")

        if not isinstance(storage, ObjectStorage):
            raise StorageNotFoundError(f"Storage '{storage_name}' is not an ObjectStorage type")

        # List all objects under prefix
        src_s3_client = S3Client(
            bucket_name=bucket_name,
            endpoint_url=source_cfg.endpoint,
            region_name=source_cfg.object_storage_region,
            aws_access_key_id=source_cfg.object_storage_access_key,
            aws_secret_access_key=source_cfg.object_storage_secret_key,
        )

        target_keys, size_map, total_bytes = await self._list_all_keys_and_sizes(
            s3_client=src_s3_client,
            prefix=key_prefix,
        )

        if not target_keys:
            raise ArtifactStorageEmptyError()

        log.trace(
            "[stream_bucket_to_bucket] start src_endpoint={} src_bucket={} src_prefix={} "
            "dst_storage={} dst_bucket={} objects={} total_bytes={} concurrency={}",
            source_cfg.endpoint,
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

        async def _copy_single_object(key: str) -> int:
            """
            Returns:
                The number of bytes copied.
            """
            async with sem:
                size = size_map.get(key, -1)
                log.trace("[stream_bucket_to_bucket] begin key={} size={}", key, size)

                download_chunk_size = storage._reservoir_download_chunk_size

                # Content-Type
                object_meta = await src_s3_client.get_object_meta(key)
                ctype = (
                    (object_meta.content_type if object_meta else None)
                    or mimetypes.guess_type(key)[0]
                    or "application/octet-stream"
                )

                data_stream = ReservoirFileDownloadStreamReader(
                    src_s3_client=src_s3_client,
                    key=key,
                    size=size,
                    options=options,
                    download_chunk_size=download_chunk_size,
                    content_type=ctype,
                )

                part_size = storage._upload_chunk_size
                await dst_client.upload_stream(
                    data_stream,
                    key,
                    part_size=part_size,
                )

                log.trace("[stream_bucket_to_bucket] done key={} bytes={}", key, size)
                return size if size >= 0 else 0

        # TODO: Replace this with global semaphore
        sizes = await asyncio.gather(*(_copy_single_object(k) for k in target_keys))
        bytes_copied = sum(sizes)

        log.trace(
            "[stream_bucket_to_bucket] all done objects={} total_bytes={}", copied, total_bytes
        )
        return bytes_copied

    async def import_model(
        self,
        registry_name: str,
        model: ModelTarget,
        storage_name: str,
        reporter: ProgressReporter,
    ) -> None:
        """
        Import a single model from a reservoir registry to a reservoir storage.

        Args:
            registry_name: Name of the Reservoir registry
            model: Reservoir model to import
            storage_name: Target storage name
            reporter: ProgressReporter for tracking progress
        """
        if model.revision is None:
            raise ArtifactRevisionEmptyError(f"Revision must be specified for model: {model}")

        if len(self._reservoir_registry_configs) == 0:
            raise ReservoirStorageConfigInvalidError("No reservoir registry configuration found.")

        reservoir_config = self._reservoir_registry_configs[0]
        prefix_key = f"{model.model_id}/{model.revision}"

        await self._stream_bucket_to_bucket(
            source_cfg=reservoir_config,
            storage_name=storage_name,
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
                revision=model.resolve_revision(ArtifactRegistryType.RESERVOIR),
                registry_name=registry_name,
                registry_type=ArtifactRegistryType.RESERVOIR,
            )
        )

    async def import_models_batch(
        self,
        registry_name: str,
        models: list[ModelTarget],
        storage_name: str,
    ) -> uuid.UUID:
        async def _import_models_batch(reporter: ProgressReporter) -> DispatchResult:
            model_count = len(models)
            if not model_count:
                log.warning("No models to import")
                return DispatchResult.error("No models provided for batch import")

            reporter.total_progress = model_count

            log.info(
                f"Starting batch model import: model_count={model_count}, "
                f"storage_name={storage_name}"
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
                            reporter=reporter,
                        )

                        successful_models += 1
                        log.info(
                            f"Successfully imported model in batch: model_id={model_id}, progress={idx}/{model_count}"
                        )
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
