import asyncio
import logging
import mimetypes
import tarfile
import tempfile
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, cast, override

import aiofiles

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import FileObjectData, ModelTarget
from ai.backend.common.data.storage.types import (
    ArtifactStorageImportStep,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import ModelImportDoneEvent
from ai.backend.common.types import DispatchResult, StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.client.manager import ManagerHTTPClient, ManagerHTTPClientArgs
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
    StorageStepRequiredStepNotProvided,
)
from ai.backend.storage.services.artifacts.storage_transfer import StorageTransferManager
from ai.backend.storage.services.artifacts.types import (
    DownloadStepResult,
    ImportPipeline,
    ImportStep,
    ImportStepContext,
)
from ai.backend.storage.storages.base import AbstractStorage
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.storages.vfs_storage import VFSStorage
from ai.backend.storage.types import BucketCopyOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReservoirVFSDownloadStreamReader(StreamReader):
    """StreamReader that wraps ManagerHTTPClient VFS download stream."""

    _client: ManagerHTTPClient
    _storage_name: str
    _filepath: str

    def __init__(
        self,
        client: ManagerHTTPClient,
        storage_name: str,
        filepath: str,
    ):
        self._client = client
        self._storage_name = storage_name
        self._filepath = filepath

    @override
    async def read(self) -> AsyncIterator[bytes]:
        async for chunk in self._client.download_vfs_file_streaming(
            self._storage_name, self._filepath
        ):
            yield chunk

    @override
    def content_type(self) -> Optional[str]:
        return "application/x-tar"


class TarExtractor:
    """Simple tar extractor that downloads and extracts VFS tar files."""

    _stream_reader: StreamReader

    def __init__(self, stream_reader: StreamReader):
        self._stream_reader = stream_reader

    async def extract_to(self, target_dir: Path) -> int:
        """
        Download tar file to temp location and extract to target directory.

        Args:
            target_dir: Directory where to extract the tar contents

        Returns:
            int: Total size of downloaded file in bytes
        """
        temp_file = None
        bytes_downloaded = 0

        try:
            # Create temporary file for tar
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tar") as tf:
                temp_file = Path(tf.name)
                log.debug(f"Downloading artifact tar to temp directory: {temp_file}")

                # Download to temp file
                async with aiofiles.open(temp_file, "wb") as f:
                    async for chunk in self._stream_reader.read():
                        await f.write(chunk)
                        bytes_downloaded += len(chunk)

                log.debug(f"Downloaded {bytes_downloaded} bytes to {temp_file}")

            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)

            # Extract tar file in executor to avoid blocking
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._extract_tar, temp_file, target_dir)

            log.info(f"Successfully extracted artifact tar to: {target_dir}")
            return bytes_downloaded

        finally:
            # Clean up temp file
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                    log.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    log.warning(f"Failed to remove temp file {temp_file}: {e}")

    def _extract_tar(self, tar_path: Path, target_dir: Path) -> None:
        """Extract tar archive to target directory."""
        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(path=target_dir)
        log.debug(f"Tar extraction completed: {tar_path} -> {target_dir}")


@dataclass
class ReservoirServiceArgs:
    background_task_manager: BackgroundTaskManager
    event_producer: EventProducer
    storage_pool: StoragePool
    reservoir_registry_configs: dict[str, ReservoirConfig]


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
    _reservoir_registry_configs: dict[str, ReservoirConfig]
    _storage_pool: StoragePool
    _transfer_manager: StorageTransferManager

    def __init__(self, args: ReservoirServiceArgs):
        self._background_task_manager = args.background_task_manager
        self._event_producer = args.event_producer
        self._reservoir_registry_configs = args.reservoir_registry_configs
        self._storage_pool = args.storage_pool
        self._transfer_manager = StorageTransferManager(args.storage_pool)

    async def import_model(
        self,
        registry_name: str,
        model: ModelTarget,
        reporter: ProgressReporter,
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
        pipeline: ImportPipeline,
    ) -> None:
        """
        Import a single model from a reservoir registry to a reservoir storage.

        Args:
            registry_name: Name of the Reservoir registry
            model: Reservoir model to import
            reporter: ProgressReporter for tracking progress
            storage_step_mappings: Mapping of import steps to storage names
        """
        success = False
        try:
            if model.revision is None:
                raise ArtifactRevisionEmptyError(f"Revision must be specified for model: {model}")

            # Create import context
            context = ImportStepContext(
                model=model,
                registry_name=registry_name,
                storage_pool=self._storage_pool,
                progress_reporter=reporter,
                storage_step_mappings=storage_step_mappings,
                step_metadata={},
            )

            # Execute import pipeline
            await pipeline.execute(context)
            log.info(f"Model import completed: {model}")
            success = True
        finally:
            await self._event_producer.anycast_event(
                ModelImportDoneEvent(
                    success=success,
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
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
        pipeline: ImportPipeline,
    ) -> uuid.UUID:
        async def _import_models_batch(reporter: ProgressReporter) -> DispatchResult:
            model_count = len(models)
            if not model_count:
                log.warning("No models to import")
                return DispatchResult.error("No models provided for batch import")

            reporter.total_progress = model_count

            log.info(f"Starting batch model import: model_count={model_count}")

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
                            registry_name=registry_name,
                            model=model,
                            reporter=reporter,
                            storage_step_mappings=storage_step_mappings,
                            pipeline=pipeline,
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


# Import Pipeline Steps


class ReservoirDownloadStep(ImportStep[None]):
    """Step to copy files from Reservoir (effectively direct copy to download storage)"""

    def __init__(
        self, registry_configs: dict[str, ReservoirConfig], download_storage: AbstractStorage
    ) -> None:
        self._registry_configs = registry_configs
        self._download_storage = download_storage

    @property
    def step_type(self) -> ArtifactStorageImportStep:
        return ArtifactStorageImportStep.DOWNLOAD

    @override
    async def execute(self, context: ImportStepContext, input_data: None) -> DownloadStepResult:
        # Get storage mapping for download step
        download_storage_name = context.storage_step_mappings.get(
            ArtifactStorageImportStep.DOWNLOAD
        )
        if not download_storage_name:
            raise StorageStepRequiredStepNotProvided("Download storage not specified in mappings")

        # Get registry configuration
        registry_config = self._registry_configs.get(context.registry_name)
        if not registry_config:
            raise ReservoirStorageConfigInvalidError(
                f"Registry configuration not found for: {context.registry_name}"
            )

        # Get the registry record to check storage_name
        # For now, we'll assume the storage_name from the registry configuration
        # In a real implementation, you'd query the database to get this information
        model = context.model
        revision = model.resolve_revision(ArtifactRegistryType.RESERVOIR)
        model_prefix = f"{model.model_id}/{revision}"

        # Determine storage type based on the actual download storage object type
        if isinstance(self._download_storage, VFSStorage):
            storage_type = "vfs"
        elif isinstance(self._download_storage, ObjectStorage):
            storage_type = "object_storage"
        else:
            storage_type = "unknown"

        bytes_copied = 0
        downloaded_files: list[tuple[FileObjectData, str]] = []

        if storage_type == "vfs":
            # Handle VFS storage type
            dest_path = (
                cast(VFSStorage, self._download_storage).base_path / model.model_id / revision
            )
            bytes_copied = await self._handle_vfs_download(
                registry_config, context, model_prefix, dest_path
            )
            # For VFS downloads, create a single entry representing the extracted archive
            file_obj = FileObjectData(
                path=str(dest_path),
                size=bytes_copied,
                type="directory",
                download_url="",  # Not applicable for VFS
            )
            downloaded_files.append((file_obj, model_prefix))
        # TODO: This only make sense when both storage are ObjectStorage
        elif storage_type == "object_storage":
            # Handle object storage type
            downloaded_files, bytes_copied = await self._handle_object_storage_download(
                registry_config, download_storage_name, context, model_prefix
            )
        else:
            raise ReservoirStorageConfigInvalidError(
                f"Unsupported storage type: {storage_type} (storage class: {type(self._download_storage)})"
            )

        log.info(f"Reservoir copy completed: {context.model}, bytes_copied={bytes_copied}")

        return DownloadStepResult(
            downloaded_files=downloaded_files,
            storage_name=download_storage_name,  # Downloaded to download storage
            total_bytes=bytes_copied,
        )

    async def _handle_vfs_download(
        self,
        registry_config: ReservoirConfig,
        context: ImportStepContext,
        model_prefix: str,
        dest_path: Path,
    ) -> int:
        """Handle file downloads for VFS storage type using ManagerHTTPClient."""

        # Use the pre-resolved download storage object
        storage = self._download_storage
        if not isinstance(storage, VFSStorage):
            raise StorageNotFoundError(
                f"Download storage is not a VFS storage type: {type(storage)}"
            )

        try:
            if (
                not registry_config.manager_endpoint
                or not registry_config.manager_access_key
                or not registry_config.manager_secret_key
                or not registry_config.manager_api_version
            ):
                raise ReservoirStorageConfigInvalidError(
                    f"Manager access key not configured for reservoir registry: {context.registry_name}"
                )

            # Create ManagerHTTPClient from config
            manager_client = ManagerHTTPClient(
                ManagerHTTPClientArgs(
                    name=context.registry_name,
                    endpoint=registry_config.manager_endpoint,
                    access_key=registry_config.manager_access_key,
                    secret_key=registry_config.manager_secret_key,
                    api_version=registry_config.manager_api_version,
                )
            )

            if not registry_config.storage_name:
                raise ReservoirStorageConfigInvalidError(
                    f"Reservoir registry storage name not configured: {context.registry_name}"
                )

            # Create stream reader that uses ManagerHTTPClient
            data_stream = ReservoirVFSDownloadStreamReader(
                client=manager_client,
                storage_name=registry_config.storage_name,
                filepath=model_prefix,
            )

            # Stream the file from reservoir VFS to target VFS storage
            return await TarExtractor(data_stream).extract_to(dest_path)

        except Exception as e:
            log.error(f"VFS download failed for {model_prefix}: {str(e)}")
            raise

    async def _handle_object_storage_download(
        self,
        registry_config: ReservoirConfig,
        download_storage_name: str,
        context: ImportStepContext,
        model_prefix: str,
    ) -> tuple[list[tuple[FileObjectData, str]], int]:
        """Handle file downloads for object storage type."""
        # Use existing object storage download logic
        options = BucketCopyOptions(
            concurrency=4,
            progress_log_interval_bytes=8 * 1024 * 1024,  # 8MB intervals
        )

        downloaded_files, bytes_copied = await self._stream_bucket_to_bucket(
            source_cfg=registry_config,
            storage_name=download_storage_name,
            storage_pool=context.storage_pool,
            options=options,
            progress_reporter=context.progress_reporter,
            key_prefix=model_prefix,
        )

        return downloaded_files, bytes_copied

    def _get_s3_client(self, storage_pool: StoragePool, storage_name: str) -> tuple[S3Client, str]:
        """Get S3 client for the specified storage"""
        # Get storage from pool and verify it's ObjectStorage type
        try:
            storage = storage_pool.get_storage(storage_name)
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

    async def _stream_bucket_to_bucket(
        self,
        source_cfg: ReservoirConfig,
        storage_name: str,
        storage_pool: StoragePool,
        options: BucketCopyOptions,
        progress_reporter: Optional[ProgressReporter],
        key_prefix: Optional[str] = None,
    ) -> tuple[list[tuple[FileObjectData, str]], int]:
        """Direct copy from Reservoir S3 to target storage"""
        dst_client, bucket_name = self._get_s3_client(storage_pool, storage_name)

        # Get storage from pool to access configuration
        try:
            storage = storage_pool.get_storage(storage_name)
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

        # Build downloaded files list
        downloaded_files: list[tuple[FileObjectData, str]] = []
        for key in target_keys:
            size = size_map.get(key, 0)
            file_obj = FileObjectData(
                path=key,
                size=size,
                type="file",
                download_url="",  # Not applicable for reservoir
            )
            downloaded_files.append((file_obj, key))

        return downloaded_files, bytes_copied

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

    @override
    async def cleanup_on_failure(self, context: ImportStepContext) -> None:
        """Clean up failed files from download storage"""
        revision = context.model.resolve_revision(ArtifactRegistryType.RESERVOIR)
        model_prefix = f"{context.model.model_id}/{revision}"

        try:
            await self._download_storage.delete_file(model_prefix)
            log.info(
                f"[cleanup] Removed failed reservoir copy from download storage: {model_prefix}"
            )
        except Exception as e:
            log.warning(
                f"[cleanup] Failed to cleanup reservoir copy from download storage: {model_prefix}: {str(e)}"
            )


class ReservoirArchiveStep(ImportStep[DownloadStepResult]):
    """Step to move downloaded files to archive storage"""

    def __init__(self, transfer_manager: StorageTransferManager) -> None:
        self._transfer_manager = transfer_manager

    @property
    def step_type(self) -> ArtifactStorageImportStep:
        return ArtifactStorageImportStep.ARCHIVE

    @override
    async def execute(self, context: ImportStepContext, input_data: DownloadStepResult) -> None:
        download_storage = input_data.storage_name
        archive_storage = context.storage_step_mappings.get(ArtifactStorageImportStep.ARCHIVE)

        if not archive_storage:
            raise StorageStepRequiredStepNotProvided("No storage mapping provided for ARCHIVE step")

        # No need to move if download and archive storage are the same
        if download_storage == archive_storage:
            log.info(
                f"Archive step skipped - download and archive storage are the same: {archive_storage}"
            )
            return

        log.info(f"Starting archive transfer: {download_storage} -> {archive_storage}")

        # Move each file from download storage to archive storage
        archieved_file_cnt = 0
        for file_info, storage_key in input_data.downloaded_files:
            archieved_file_cnt += await self._transfer_manager.transfer_directory(
                source_storage_name=download_storage,
                dest_storage_name=archive_storage,
                source_prefix=storage_key,
                dest_prefix=storage_key,
            )
            log.debug(f"Transferred file to archive: {storage_key}")

        log.info(
            f"Archive transfer completed: {download_storage} -> {archive_storage}, "
            f"files={archieved_file_cnt}"
        )

    @override
    async def cleanup_on_failure(self, context: ImportStepContext) -> None:
        """Clean up failed files from archive storage"""
        archive_storage = context.storage_step_mappings.get(ArtifactStorageImportStep.ARCHIVE)
        if not archive_storage:
            return

        # Delete entire model (cleaning up individual files is complex)
        revision = context.model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        model_prefix = f"{context.model.model_id}/{revision}"

        try:
            storage = context.storage_pool.get_storage(archive_storage)
            await storage.delete_file(model_prefix)
            log.info(f"[cleanup] Removed failed archive: {archive_storage}:{model_prefix}")
        except Exception as e:
            log.warning(
                f"[cleanup] Failed to cleanup archive: {archive_storage}:{model_prefix}: {str(e)}"
            )


def create_reservoir_import_pipeline(
    storage_pool: StoragePool,
    registry_configs: dict[str, Any],
    storage_step_mappings: dict[ArtifactStorageImportStep, str],
    transfer_manager: StorageTransferManager,
) -> ImportPipeline:
    """Create ImportPipeline for Reservoir based on storage step mappings."""
    steps: list[ImportStep[Any]] = []

    # Add steps based on what's present in storage_step_mappings
    if ArtifactStorageImportStep.DOWNLOAD in storage_step_mappings:
        # Get the download storage object from the pool
        download_storage_name = storage_step_mappings.get(ArtifactStorageImportStep.DOWNLOAD)
        if not download_storage_name:
            raise StorageStepRequiredStepNotProvided("Download storage not specified in mappings")

        download_storage = storage_pool.get_storage(download_storage_name)
        steps.append(ReservoirDownloadStep(registry_configs, download_storage))

    if ArtifactStorageImportStep.ARCHIVE in storage_step_mappings:
        steps.append(ReservoirArchiveStep(transfer_manager))

    return ImportPipeline(steps)
