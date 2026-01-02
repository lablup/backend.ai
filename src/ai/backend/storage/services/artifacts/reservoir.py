import asyncio
import logging
import mimetypes
import tarfile
import tempfile
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Optional, cast, override

import aiofiles
import aiohttp

from ai.backend.common.artifact_storage import AbstractStorage, AbstractStoragePool
from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    VerificationStepResult,
)
from ai.backend.common.data.storage.registries.types import FileObjectData, ModelTarget
from ai.backend.common.data.storage.types import (
    ArtifactStorageImportStep,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import ModelImportDoneEvent
from ai.backend.common.types import DispatchResult, StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.client.manager import ManagerHTTPClient, ManagerHTTPClientPool
from ai.backend.storage.client.s3 import S3Client
from ai.backend.storage.config.unified import (
    ReservoirConfig,
)
from ai.backend.storage.context_types import ArtifactVerifierContext
from ai.backend.storage.errors import (
    ArtifactRevisionEmptyError,
    ArtifactStorageEmptyError,
    ObjectStorageBucketNotFoundError,
    ReservoirStorageConfigInvalidError,
    StorageNotFoundError,
    StorageStepRequiredStepNotProvided,
)
from ai.backend.storage.services.artifacts.common import ModelArchiveStep, ModelVerifyStep
from ai.backend.storage.services.artifacts.storage_transfer import StorageTransferManager
from ai.backend.storage.services.artifacts.types import (
    DownloadStepResult,
    ImportPipeline,
    ImportStep,
    ImportStepContext,
)
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.storages.vfs_storage import VFSStorage
from ai.backend.storage.types import BucketCopyOptions

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DOWNLOAD_PROGRESS_UPDATE_INTERVAL: Final[int] = 30


class ReservoirVFSDownloadStreamReader(StreamReader):
    """StreamReader that wraps ManagerHTTPClient VFS download stream for individual files."""

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
        # Guess content type from file extension
        content_type, _ = mimetypes.guess_type(self._filepath)
        return content_type or "application/octet-stream"


class ReservoirVFSFileDownloader:
    """Helper class to download individual files from VFS storage to local filesystem."""

    _client: ManagerHTTPClient
    _storage_name: str
    _redis_client: ValkeyArtifactDownloadTrackingClient
    _model_id: str
    _revision: str
    _download_complete: bool
    _progress_task: Optional[asyncio.Task[None]]
    _bytes_downloaded: int

    def __init__(
        self,
        client: ManagerHTTPClient,
        storage_name: str,
        redis_client: ValkeyArtifactDownloadTrackingClient,
        model_id: str,
        revision: str,
    ):
        self._client = client
        self._storage_name = storage_name
        self._redis_client = redis_client
        self._model_id = model_id
        self._revision = revision
        self._download_complete = False
        self._progress_task = None
        self._bytes_downloaded = 0

    async def _periodic_progress_update(
        self,
        total_bytes: int,
        file_path: str,
    ) -> None:
        """
        Background task that periodically updates Redis with download progress.

        :param total_bytes: Total bytes for this file
        :param file_path: Path of the file being downloaded
        """
        while not self._download_complete:
            await asyncio.sleep(_DOWNLOAD_PROGRESS_UPDATE_INTERVAL)

            try:
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=file_path,
                    current_bytes=self._bytes_downloaded,
                    total_bytes=total_bytes,
                    success=False,
                )
            except asyncio.CancelledError:
                # Task is being cancelled, exit cleanly
                break
            except Exception as e:
                # Log error but don't fail the download
                log.warning(
                    "Failed to update download progress in Redis: {}",
                    str(e),
                )

    async def download_file(self, remote_path: str, local_path: Path, total_bytes: int) -> int:
        """
        Download a single file from VFS storage to local filesystem.

        Args:
            remote_path: Path of the file in VFS storage
            local_path: Local filesystem path to save the file
            total_bytes: Total size of the file in bytes

        Returns:
            Number of bytes downloaded
        """
        # Ensure parent directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize download state
        self._bytes_downloaded = 0
        self._download_complete = False
        self._progress_task = None

        stream_reader = ReservoirVFSDownloadStreamReader(
            self._client, self._storage_name, remote_path
        )

        try:
            # Start background progress task
            self._progress_task = asyncio.create_task(
                self._periodic_progress_update(
                    total_bytes=total_bytes,
                    file_path=remote_path,
                )
            )

            async with aiofiles.open(local_path, "wb") as f:
                try:
                    async for chunk in stream_reader.read():
                        await f.write(chunk)
                        self._bytes_downloaded += len(chunk)
                except aiohttp.ClientError as e:
                    log.error(
                        f"Network error during download: {e}, Downloaded {self._bytes_downloaded} bytes before failure"
                    )
                    raise
                except asyncio.TimeoutError:
                    log.error(f"Timeout after downloading {self._bytes_downloaded} bytes")
                    raise
        except Exception as e:
            # Update Redis with error status for any unexpected errors
            try:
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=remote_path,
                    current_bytes=self._bytes_downloaded,
                    total_bytes=total_bytes,
                    success=False,
                    error_message=str(e),
                )
            except Exception as redis_err:
                log.warning(f"Failed to update error status in Redis: {redis_err}")
            raise
        finally:
            self._download_complete = True

            # Cancel and wait for progress task
            if self._progress_task:
                self._progress_task.cancel()
                try:
                    await self._progress_task
                except asyncio.CancelledError:
                    pass

            # Final update to Redis with success status
            try:
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=remote_path,
                    current_bytes=self._bytes_downloaded,
                    total_bytes=total_bytes,
                    success=(self._bytes_downloaded >= total_bytes),
                )
            except Exception as redis_err:
                log.warning(f"Failed to update final status in Redis: {redis_err}")

        log.debug(
            f"Downloaded file: {remote_path} -> {local_path} ({self._bytes_downloaded} bytes)"
        )
        return self._bytes_downloaded


class ReservoirS3FileDownloadStreamReader(StreamReader):
    _src_s3_client: S3Client
    _key: str
    _size: int
    _options: BucketCopyOptions
    _download_chunk_size: int
    _content_type: Optional[str]
    _redis_client: ValkeyArtifactDownloadTrackingClient
    _model_id: str
    _revision: str
    _download_complete: bool
    _progress_task: Optional[asyncio.Task[None]]

    def __init__(
        self,
        src_s3_client: S3Client,
        key: str,
        size: int,
        options: BucketCopyOptions,
        download_chunk_size: int,
        content_type: Optional[str],
        redis_client: ValkeyArtifactDownloadTrackingClient,
        model_id: str,
        revision: str,
    ):
        self._src_s3_client = src_s3_client
        self._key = key
        self._size = size
        self._options = options
        self._download_chunk_size = download_chunk_size
        self._content_type = content_type
        self._redis_client = redis_client
        self._model_id = model_id
        self._revision = revision
        self._download_complete = False
        self._progress_task = None

    async def _periodic_progress_update(
        self,
        offset_getter: Callable[[], int],
        total_bytes: int,
    ) -> None:
        """
        Background task that periodically updates Redis with download progress.

        :param offset_getter: Callable that returns current download offset
        :param total_bytes: Total bytes for this file
        """
        while not self._download_complete:
            await asyncio.sleep(_DOWNLOAD_PROGRESS_UPDATE_INTERVAL)

            try:
                current = offset_getter()
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=self._key,
                    current_bytes=current,
                    total_bytes=total_bytes,
                    success=False,
                )
            except asyncio.CancelledError:
                # Task is being cancelled, exit cleanly
                break
            except Exception as e:
                # Log error but don't fail the download
                log.warning(
                    "Failed to update download progress in Redis: {}",
                    str(e),
                )

    @override
    async def read(self) -> AsyncIterator[bytes]:
        sent = 0
        next_mark = self._options.progress_log_interval_bytes
        download_stream = self._src_s3_client.download_stream(
            self._key, chunk_size=self._download_chunk_size
        )

        self._download_complete = False
        self._progress_task = None

        try:
            # Start background progress task
            self._progress_task = asyncio.create_task(
                self._periodic_progress_update(
                    offset_getter=lambda: sent,
                    total_bytes=self._size,
                )
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
        except Exception as e:
            # Update Redis with error status
            try:
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=self._key,
                    current_bytes=sent,
                    total_bytes=self._size,
                    success=False,
                    error_message=str(e),
                )
            except Exception as redis_err:
                log.warning(f"Failed to update error status in Redis: {redis_err}")
            raise
        finally:
            self._download_complete = True

            # Cancel and wait for progress task
            if self._progress_task:
                self._progress_task.cancel()
                try:
                    await self._progress_task
                except asyncio.CancelledError:
                    pass

            # Final update to Redis with success status
            try:
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=self._key,
                    current_bytes=sent,
                    total_bytes=self._size,
                    success=(sent >= self._size),
                )
            except Exception as redis_err:
                log.warning(f"Failed to update final status in Redis: {redis_err}")

    @override
    def content_type(self) -> Optional[str]:
        return self._content_type


@dataclass
class ReservoirServiceArgs:
    background_task_manager: BackgroundTaskManager
    event_producer: EventProducer
    storage_pool: StoragePool
    reservoir_registry_configs: dict[str, ReservoirConfig]
    artifact_verifier_ctx: ArtifactVerifierContext
    manager_client_pool: ManagerHTTPClientPool
    redis_client: ValkeyArtifactDownloadTrackingClient


class ReservoirService:
    """Service for Reservoir model operations"""

    _background_task_manager: BackgroundTaskManager
    _event_producer: EventProducer
    _reservoir_registry_configs: dict[str, ReservoirConfig]
    _storage_pool: StoragePool
    _transfer_manager: StorageTransferManager
    _artifact_verifier_ctx: ArtifactVerifierContext
    _manager_client_pool: ManagerHTTPClientPool
    _redis_client: ValkeyArtifactDownloadTrackingClient

    def __init__(self, args: ReservoirServiceArgs):
        self._background_task_manager = args.background_task_manager
        self._event_producer = args.event_producer
        self._reservoir_registry_configs = args.reservoir_registry_configs
        self._storage_pool = args.storage_pool
        self._transfer_manager = StorageTransferManager(args.storage_pool)
        self._artifact_verifier_ctx = args.artifact_verifier_ctx
        self._manager_client_pool = args.manager_client_pool
        self._redis_client = args.redis_client

    async def _fetch_remote_verification_result(
        self,
        registry_name: str,
        artifact_revision_id: uuid.UUID,
    ) -> Optional[VerificationStepResult]:
        """
        Fetch verification result from remote reservoir manager.

        Args:
            registry_name: Name of the Reservoir registry
            artifact_revision_id: The artifact revision ID to get verification result for

        Returns:
            VerificationStepResult if available, None otherwise
        """
        manager_client = self._manager_client_pool.get_or_create(registry_name)

        try:
            log.debug(
                f"Querying verification result from remote reservoir for artifact revision {artifact_revision_id}"
            )
            resp = await manager_client.get_verification_result(artifact_revision_id)
            if resp.verification_result:
                log.info(
                    "Fetched verification result from remote reservoir: artifact_revision_id={}",
                    artifact_revision_id,
                )
            return resp.verification_result
        except Exception as e:
            log.warning(
                "Failed to fetch verification result from remote reservoir: "
                "artifact_revision_id={}, error={}",
                artifact_revision_id,
                str(e),
            )
            return None

    async def import_model(
        self,
        registry_name: str,
        model: ModelTarget,
        reporter: ProgressReporter,
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
        pipeline: ImportPipeline,
        artifact_revision_id: uuid.UUID,
    ) -> None:
        """
        Import a single model from a reservoir registry to a reservoir storage.

        Args:
            registry_name: Name of the Reservoir registry
            model: Reservoir model to import
            reporter: ProgressReporter for tracking progress
            storage_step_mappings: Mapping of import steps to storage names
            pipeline: ImportPipeline to execute
            artifact_revision_id: The artifact revision ID for verification result lookup
        """
        success = False
        verification_result: Optional[VerificationStepResult] = None
        try:
            if model.revision is None:
                raise ArtifactRevisionEmptyError(f"Revision must be specified for model: {model}")

            # Create import context
            context = ImportStepContext(
                model=model,
                registry_name=registry_name,
                storage_pool=self._storage_pool,
                storage_step_mappings=storage_step_mappings,
                step_metadata={},
            )

            # Execute import pipeline
            await pipeline.execute(context)
            log.info(f"Model import completed: {model}")
            success = True

            # Fetch verification result from remote reservoir
            verification_result = await self._fetch_remote_verification_result(
                registry_name, artifact_revision_id
            )
        finally:
            await self._event_producer.anycast_event(
                ModelImportDoneEvent(
                    success=success,
                    model_id=model.model_id,
                    revision=model.resolve_revision(ArtifactRegistryType.RESERVOIR),
                    registry_name=registry_name,
                    registry_type=ArtifactRegistryType.RESERVOIR,
                    # Reservoir registry's artifact's digest will be synced through scan API later
                    digest=None,
                    verification_result=verification_result,
                )
            )

    async def import_models_batch(
        self,
        registry_name: str,
        models: list[ModelTarget],
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
        pipeline: ImportPipeline,
        artifact_revision_ids: list[uuid.UUID],
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
                for idx, (model, artifact_revision_id) in enumerate(
                    zip(models, artifact_revision_ids, strict=True), 1
                ):
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
                            artifact_revision_id=artifact_revision_id,
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
        self,
        registry_configs: dict[str, ReservoirConfig],
        download_storage: AbstractStorage,
        manager_client_pool: ManagerHTTPClientPool,
        redis_client: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        self._registry_configs = registry_configs
        self._download_storage = download_storage
        self._manager_client_pool = manager_client_pool
        self._redis_client = redis_client

    @property
    def step_type(self) -> ArtifactStorageImportStep:
        return ArtifactStorageImportStep.DOWNLOAD

    @property
    @override
    def registry_type(self) -> ArtifactRegistryType:
        return ArtifactRegistryType.RESERVOIR

    @override
    def stage_storage(self, context: ImportStepContext) -> AbstractStorage:
        return self._download_storage

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
        """Handle file downloads for VFS storage type using individual file downloads."""

        # Use the pre-resolved download storage object
        storage = self._download_storage
        if not isinstance(storage, VFSStorage):
            raise StorageNotFoundError(
                f"Download storage is not a VFS storage type: {type(storage)}"
            )

        try:
            manager_client = self._manager_client_pool.get_or_create(context.registry_name)

            if not registry_config.storage_name:
                raise ReservoirStorageConfigInvalidError(
                    f"Reservoir registry storage name not configured: {context.registry_name}"
                )

            # Get list of all files in the model directory
            log.debug(f"Listing files for model: {model_prefix}")
            file_list_response = await manager_client.list_vfs_files(
                storage_name=registry_config.storage_name, directory=model_prefix
            )

            files = file_list_response.files
            if not files:
                log.warning(f"No files found for model: {model_prefix}")
                return 0

            log.info(f"Found {len(files)} files to download for model: {model_prefix}")

            # Initialize artifact download tracking in Redis with all file information
            revision = context.model.resolve_revision(ArtifactRegistryType.RESERVOIR)
            file_info_list = [
                (file_info.path, file_info.size or 0)
                for file_info in files
                if file_info.type != "directory"
            ]
            await self._redis_client.init_artifact_download(
                model_id=context.model.model_id,
                revision=revision,
                file_info_list=file_info_list,
            )

            # Create file downloader
            downloader = ReservoirVFSFileDownloader(
                client=manager_client,
                storage_name=registry_config.storage_name,
                redis_client=self._redis_client,
                model_id=context.model.model_id,
                revision=revision,
            )

            # Download each file individually
            total_bytes = 0
            for file_info in files:
                # Skip directories (they will be created automatically when files are downloaded)
                if file_info.type == "directory":
                    continue

                remote_file_path = file_info.path
                # Convert remote path to local path relative to dest_path
                # Remove model_prefix from the beginning to get relative path within model
                if remote_file_path.startswith(model_prefix):
                    relative_path = remote_file_path[len(model_prefix) :].lstrip("/")
                else:
                    relative_path = remote_file_path

                local_file_path = dest_path / relative_path
                bytes_downloaded = await downloader.download_file(
                    remote_file_path, local_file_path, file_info.size or 0
                )
                total_bytes += bytes_downloaded
                log.debug(f"Downloaded: {remote_file_path} ({bytes_downloaded} bytes)")

            log.info(f"VFS download completed: {model_prefix} -> {dest_path} ({total_bytes} bytes)")
            return total_bytes

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

        # Initialize artifact download tracking
        revision = context.model.resolve_revision(ArtifactRegistryType.RESERVOIR)

        downloaded_files, bytes_copied = await self._stream_bucket_to_bucket(
            source_cfg=registry_config,
            storage_name=download_storage_name,
            storage_pool=context.storage_pool,
            options=options,
            model_id=context.model.model_id,
            revision=revision,
            progress_reporter=None,
            key_prefix=model_prefix,
        )

        return downloaded_files, bytes_copied

    def _get_s3_client(
        self, storage_pool: AbstractStoragePool, storage_name: str
    ) -> tuple[S3Client, str]:
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
        storage_pool: AbstractStoragePool,
        options: BucketCopyOptions,
        model_id: str,
        revision: str,
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

        # Initialize artifact download tracking in Redis with all file information
        file_info_list = [(key, size_map.get(key, 0)) for key in target_keys]
        await self._redis_client.init_artifact_download(
            model_id=model_id,
            revision=revision,
            file_info_list=file_info_list,
        )

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

                data_stream = ReservoirS3FileDownloadStreamReader(
                    src_s3_client=src_s3_client,
                    key=key,
                    size=size,
                    options=options,
                    download_chunk_size=download_chunk_size,
                    content_type=ctype,
                    redis_client=self._redis_client,
                    model_id=model_id,
                    revision=revision,
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


class ReservoirVerifyStep(ModelVerifyStep):
    """Step to verify downloaded files in Reservoir model import"""

    @property
    @override
    def registry_type(self) -> ArtifactRegistryType:
        return ArtifactRegistryType.RESERVOIR


class ReservoirArchiveStep(ModelArchiveStep):
    """Step to move downloaded files to archive storage"""

    @property
    @override
    def registry_type(self) -> ArtifactRegistryType:
        return ArtifactRegistryType.RESERVOIR


# Utilities


def create_reservoir_import_pipeline(
    storage_pool: StoragePool,
    registry_configs: dict[str, Any],
    storage_step_mappings: dict[ArtifactStorageImportStep, str],
    transfer_manager: StorageTransferManager,
    artifact_verifier_ctx: ArtifactVerifierContext,
    event_producer: EventProducer,
    manager_client_pool: ManagerHTTPClientPool,
    redis_client: ValkeyArtifactDownloadTrackingClient,
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
        steps.append(
            ReservoirDownloadStep(
                registry_configs,
                download_storage,
                manager_client_pool,
                redis_client,
            )
        )

    if ArtifactStorageImportStep.VERIFY in storage_step_mappings:
        steps.append(ReservoirVerifyStep(artifact_verifier_ctx, transfer_manager, event_producer))

    if ArtifactStorageImportStep.ARCHIVE in storage_step_mappings:
        steps.append(ReservoirArchiveStep(transfer_manager))

    return ImportPipeline(steps)


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
        """Extract tar archive to target directory safely."""
        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(path=target_dir, filter=tarfile.data_filter)
        log.debug(f"Tar extraction completed: {tar_path} -> {target_dir}")
