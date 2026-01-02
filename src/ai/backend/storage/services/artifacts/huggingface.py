from __future__ import annotations

import asyncio
import logging
import mimetypes
import ssl
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Callable, Final, Optional, override

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
from ai.backend.common.data.storage.registries.types import (
    FileObjectData,
    ModelData,
    ModelSortKey,
    ModelTarget,
)
from ai.backend.common.data.storage.types import (
    ArtifactStorageImportStep,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import ModelImportDoneEvent
from ai.backend.common.types import DispatchResult, StreamReader
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.client.huggingface import (
    HuggingFaceClient,
    HuggingFaceClientArgs,
    HuggingFaceScanner,
)
from ai.backend.storage.config.unified import HuggingfaceConfig
from ai.backend.storage.context_types import ArtifactVerifierContext
from ai.backend.storage.errors import (
    HuggingFaceAPIError,
    HuggingFaceModelNotFoundError,
    ObjectStorageConfigInvalidError,
    RegistryNotFoundError,
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
from ai.backend.storage.storages.storage_pool import StoragePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_MiB = 1024 * 1024

_DOWNLOAD_PROGRESS_UPDATE_INTERVAL: Final[int] = 30
_PROBE_HEAD_BASE_HEADER: Final[dict[str, str]] = {"Accept-Encoding": "identity"}

_DOWNLOAD_RETRIABLE_ERROR = (
    aiohttp.ClientPayloadError,
    aiohttp.ServerDisconnectedError,
    aiohttp.ClientOSError,
    asyncio.TimeoutError,
    ssl.SSLError,
)


@dataclass
class _ProbeHeadInfo:
    total: int
    etag: Optional[str]
    accept_ranges: bool


class HuggingFaceFileDownloadStreamReader(StreamReader):
    _url: str
    _chunk_size: int
    _max_retries: int
    _content_type: Optional[str]
    _redis_client: ValkeyArtifactDownloadTrackingClient
    _model_id: str
    _revision: str
    _file_path: str
    _download_complete: bool
    _progress_task: Optional[asyncio.Task[None]]
    _token: Optional[str]

    def __init__(
        self,
        url: str,
        chunk_size: int,
        max_retries: int,
        content_type: Optional[str],
        redis_client: ValkeyArtifactDownloadTrackingClient,
        model_id: str,
        revision: str,
        file_path: str,
        token: Optional[str] = None,
    ) -> None:
        self._url = url
        self._chunk_size = chunk_size
        self._max_retries = max_retries
        self._content_type = content_type
        self._redis_client = redis_client
        self._model_id = model_id
        self._revision = revision
        self._file_path = file_path
        self._download_complete = False
        self._progress_task = None
        self._token = token

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
                    file_path=self._file_path,
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

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers if token is available."""
        headers = dict(_PROBE_HEAD_BASE_HEADER)
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _probe_head(self) -> _ProbeHeadInfo:
        """
        Probe metadata via HEAD.
        - Sets total size, etag, and Accept-Ranges support.
        - Raises error if Content-Length is not available.
        """
        headers_base = self._get_auth_headers()
        async with self._session.head(
            self._url,
            headers=headers_base,
            allow_redirects=True,
        ) as resp:
            content_length = resp.headers.get("Content-Length")
            if not content_length or not content_length.isdigit():
                raise aiohttp.ClientPayloadError(
                    f"Content-Length header missing or invalid in HEAD response for {self._url}"
                )
            total = int(content_length)

            etag = resp.headers.get("ETag")
            accept_ranges = "bytes" in (resp.headers.get("Accept-Ranges", "")).lower()

        return _ProbeHeadInfo(total=total, etag=etag, accept_ranges=accept_ranges)

    @override
    async def read(self) -> AsyncIterator[bytes]:
        """
        Stream bytes from `url`.
        """
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None, sock_read=None),
            auto_decompress=False,
            raise_for_status=True,
        )

        headers_base = self._get_auth_headers()

        offset = 0
        backoff = 1.0
        retries = 0

        self._download_complete = False
        self._progress_task = None

        # Probe head first - if this fails, we can't proceed
        probe_info = await self._probe_head()
        total = probe_info.total
        etag = probe_info.etag
        accept_ranges = probe_info.accept_ranges

        try:
            # Start background progress task
            self._progress_task = asyncio.create_task(
                self._periodic_progress_update(
                    offset_getter=lambda: offset,
                    total_bytes=total,
                )
            )

            while True:
                headers = dict(headers_base)
                if offset and accept_ranges:
                    headers["Range"] = f"bytes={offset}-"

                try:
                    async with self._session.get(
                        self._url, headers=headers, allow_redirects=True
                    ) as resp:
                        # Validate partial content when resuming
                        if offset and accept_ranges and resp.status != 206:
                            raise aiohttp.ClientPayloadError(f"Expected 206, got {resp.status}")

                        # Validate ETag across resumes
                        resp_etag = resp.headers.get("ETag")
                        if etag and resp_etag and resp_etag != etag:
                            raise aiohttp.ClientPayloadError("ETag changed during resume")

                        async for chunk in resp.content.iter_chunked(self._chunk_size):
                            if not chunk:
                                continue
                            offset += len(chunk)
                            yield chunk

                    # Completed
                    if offset >= total:
                        break

                    # Unexpected early EOF → retry
                    raise aiohttp.ClientPayloadError("Early EOF before Content-Length")

                except _DOWNLOAD_RETRIABLE_ERROR as e:
                    retries += 1
                    if retries > self._max_retries:
                        raise aiohttp.ClientPayloadError(
                            f"Exceeded retries while downloading {self._url} at offset={offset}"
                        ) from e

                    log.warning(
                        "Download retry {}/{} at offset {:.1f} MiB (backoff={:.1f}s, err={})",
                        retries,
                        self._max_retries,
                        offset / _MiB,
                        backoff,
                        e.__class__.__name__,
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)

                    # Refresh metadata before retry
                    probe_info = await self._probe_head()
                    total = probe_info.total
                    etag = probe_info.etag
                    accept_ranges = probe_info.accept_ranges
                    continue
        except Exception as e:
            # Update Redis with error status
            try:
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=self._file_path,
                    current_bytes=offset,
                    total_bytes=total,
                    success=False,
                    error_message=str(e),
                )
            except Exception as redis_err:
                log.warning("Failed to update error status in Redis: {}", str(redis_err))
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

            # Final update to Redis
            try:
                await self._redis_client.update_file_progress(
                    model_id=self._model_id,
                    revision=self._revision,
                    file_path=self._file_path,
                    current_bytes=offset,
                    total_bytes=total,
                    success=(offset >= total),
                )
            except Exception as redis_err:
                log.warning("Failed to update final status in Redis: {}", str(redis_err))

            await self._session.close()

    @override
    def content_type(self) -> Optional[str]:
        return self._content_type


@dataclass
class HuggingFaceServiceArgs:
    registry_configs: dict[str, HuggingfaceConfig]
    background_task_manager: BackgroundTaskManager
    storage_pool: StoragePool
    event_producer: EventProducer
    artifact_verifier_ctx: ArtifactVerifierContext
    redis_client: ValkeyArtifactDownloadTrackingClient


class HuggingFaceService:
    """Service for HuggingFace model operations"""

    _storage_pool: StoragePool
    _background_task_manager: BackgroundTaskManager
    _registry_configs: dict[str, HuggingfaceConfig]
    _event_producer: EventProducer
    _transfer_manager: StorageTransferManager
    _artifact_verifier_ctx: ArtifactVerifierContext
    _redis_client: ValkeyArtifactDownloadTrackingClient

    def __init__(self, args: HuggingFaceServiceArgs):
        self._storage_pool = args.storage_pool
        self._background_task_manager = args.background_task_manager
        self._registry_configs = args.registry_configs
        self._event_producer = args.event_producer
        self._transfer_manager = StorageTransferManager(args.storage_pool)
        self._artifact_verifier_ctx = args.artifact_verifier_ctx
        self._redis_client = args.redis_client

    def _make_scanner(self, registry_name: str) -> HuggingFaceScanner:
        config = self._registry_configs.get(registry_name)
        if not config:
            raise RegistryNotFoundError(f"HuggingFace registry not found: {registry_name}")

        client = HuggingFaceClient(
            HuggingFaceClientArgs(
                token=config.token,
                endpoint=config.endpoint,
            )
        )
        scanner = HuggingFaceScanner(client)
        return scanner

    async def scan_models(
        self,
        registry_name: str,
        limit: int,
        sort: ModelSortKey,
        search: Optional[str] = None,
    ) -> list[ModelData]:
        """List HuggingFace models with metadata.

        Args:
            registry_name: Name of the HuggingFace registry
            limit: Maximum number of models to retrieve
            search: Search query to filter models
            sort: Sort criteria ("downloads", "likes", "created_at", "last_modified")

        Returns:
            UUID of the background task that will perform the scan

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Scanning HuggingFace models: limit={limit}, search={search}, sort={sort}")

        models = await self._make_scanner(registry_name).scan_models(
            limit=limit, search=search, sort=sort
        )

        # Start background task to download metadata and fire event when complete
        if models:
            scanner = self._make_scanner(registry_name)
            asyncio.create_task(
                scanner.download_metadata_batch(models, registry_name, self._event_producer)
            )

        return models

    async def retrieve_model(
        self,
        registry_name: str,
        model: ModelTarget,
    ) -> ModelData:
        """
        Retrieve specific model by their model_id and revision.
        For single model, fetch metadata immediately with full data

        Args:
            registry_name: Name of the HuggingFace registry
            model: ModelTarget object with model_id and revision

        Returns:
            List of ModelData objects with complete metadata

        Raises:
            HuggingFaceModelNotFoundError: If any model is not found
            HuggingFaceAPIError: If API call fails
        """
        log.info("Retrieving single HuggingFace model: {}", model)
        scanner = self._make_scanner(registry_name)
        model_data = await scanner.scan_model(model)
        log.debug(f"Successfully retrieved single model with metadata: {model}")
        return model_data

    async def get_model_commit_hash(
        self,
        registry_name: str,
        model: ModelTarget,
    ) -> Optional[str]:
        """Get the commit hash for a specific model revision.

        Args:
            registry_name: Name of the HuggingFace registry
            model: Model target with specific revision

        Returns:
            The commit hash (SHA) for the model revision, or None if not available
        """
        scanner = self._make_scanner(registry_name)
        return await scanner._client.get_model_commit_hash(model)

    async def retrieve_models(
        self,
        registry_name: str,
        models: list[ModelTarget],
    ) -> list[ModelData]:
        """Retrieve specific models by their model_id and revision.

        Args:
            registry_name: Name of the HuggingFace registry
            models: List of ModelTarget objects with model_id and revision

        Returns:
            List of ModelData objects with complete metadata

        Raises:
            HuggingFaceModelNotFoundError: If any model is not found
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Retrieving {len(models)} HuggingFace models")

        scanner = self._make_scanner(registry_name)
        retrieved_models = []
        # For multiple models, get basic model data first then start background metadata processing
        for model in models:
            try:
                model_data = await scanner.scan_model_without_metadata(model)
                retrieved_models.append(model_data)
                log.debug(f"Successfully retrieved basic model data: {model}")
            except Exception as e:
                log.error(f"Failed to retrieve model {model}: {str(e)}")
                raise

        # Start background metadata processing for multiple models
        if retrieved_models:
            asyncio.create_task(
                scanner.download_metadata_batch(
                    retrieved_models, registry_name, self._event_producer
                )
            )

        log.info(f"Successfully retrieved {len(retrieved_models)} models")
        return retrieved_models

    async def scan_model(self, registry_name: str, model: ModelTarget) -> ModelData:
        """Get detailed information about a specific model.

        Args:
            registry_name: Name of the HuggingFace registry
            model: ModelTarget containing model_id and revision

        Returns:
            ModelData object with complete metadata

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Scanning HuggingFace model: {model}")
        return await self._make_scanner(registry_name).scan_model(model)

    async def list_model_files(
        self, registry_name: str, model: ModelTarget
    ) -> list[FileObjectData]:
        """List all files in a specific model.

        Args:
            registry_name: Name of the HuggingFace registry
            model: ModelTarget containing model_id and revision

        Returns:
            List of FileInfo objects

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Listing model files: {model}")
        return await self._make_scanner(registry_name).list_model_files_info(model)

    def get_download_url(self, registry_name: str, model: ModelTarget, filename: str) -> str:
        """Get download URL for a specific file.

        Args:
            registry_name: Name of the HuggingFace registry
            model: ModelTarget containing model_id and revision
            filename: File name within the model

        Returns:
            Download URL string
        """
        log.info(f"Getting download URL: {model}, filename={filename}")
        return self._make_scanner(registry_name).get_download_url(model, filename)

    async def import_model(
        self,
        registry_name: str,
        model: ModelTarget,
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
        pipeline: ImportPipeline,
    ) -> None:
        """Import a HuggingFace model to storage using ImportPipeline.

        Args:
            registry_name: Name of the HuggingFace registry
            model: HuggingFace model to import
            storage_step_mappings: Mapping of import steps to storage names
            pipeline: ImportPipeline configured for this request

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        success = False
        verification_result: Optional[VerificationStepResult] = None
        try:
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
            success = True

            # Extract verification result from context (None if verification step was not executed)
            verification_result = context.step_metadata.get("verification_result")

            log.info(f"Model import completed: {model}")
        except HuggingFaceModelNotFoundError:
            raise
        except Exception as e:
            raise HuggingFaceAPIError(f"Import failed for {model}: {str(e)}") from e
        finally:
            scanner = self._make_scanner(registry_name)
            commit_hash = None
            if success:
                commit_hash = await scanner.get_model_commit_hash(model)

            await self._event_producer.anycast_event(
                ModelImportDoneEvent(
                    success=success,
                    model_id=model.model_id,
                    revision=model.resolve_revision(ArtifactRegistryType.HUGGINGFACE),
                    registry_name=registry_name,
                    registry_type=ArtifactRegistryType.HUGGINGFACE,
                    digest=commit_hash,
                    verification_result=verification_result,
                )
            )

    async def _download_readme_content(self, download_url: str) -> Optional[str]:
        """Download README content from the given URL.

        Args:
            download_url: The URL to download README content from

        Returns:
            README content as string if successful, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    else:
                        log.warning(f"Failed to download README.md: HTTP {resp.status}")
                        return None
        except Exception as e:
            log.error(f"Error downloading README.md: {str(e)}")
            return None

    async def import_models_batch(
        self,
        registry_name: str,
        models: list[ModelTarget],
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
        pipeline: ImportPipeline,
    ) -> uuid.UUID:
        """Import multiple HuggingFace models to storage in batch.

        Args:
            registry_name: Name of the HuggingFace registry
            models: List of HuggingFace models to import

        Raises:
            HuggingFaceAPIError: If API call fails
        """

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

                        await self.import_model(
                            registry_name=registry_name,
                            model=model,
                            storage_step_mappings=storage_step_mappings,
                            pipeline=pipeline,
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


# Import Pipeline Steps


class HuggingFaceDownloadStep(ImportStep[None]):
    """Step to download files from HuggingFace"""

    def __init__(
        self,
        registry_configs: dict[str, HuggingfaceConfig],
        redis_client: ValkeyArtifactDownloadTrackingClient,
    ) -> None:
        self._registry_configs = registry_configs
        self._redis_client = redis_client

    @property
    def step_type(self) -> ArtifactStorageImportStep:
        return ArtifactStorageImportStep.DOWNLOAD

    @property
    @override
    def registry_type(self) -> ArtifactRegistryType:
        return ArtifactRegistryType.HUGGINGFACE

    @override
    def stage_storage(self, context: ImportStepContext) -> AbstractStorage:
        download_storage_name = context.storage_step_mappings.get(
            ArtifactStorageImportStep.DOWNLOAD
        )
        if not download_storage_name:
            raise StorageStepRequiredStepNotProvided(
                "No storage mapping provided for DOWNLOAD step cleanup"
            )

        return context.storage_pool.get_storage(download_storage_name)

    def _make_scanner(self, registry_name: str) -> HuggingFaceScanner:
        config = self._registry_configs.get(registry_name)
        if not config:
            raise RegistryNotFoundError(f"HuggingFace registry not found: {registry_name}")

        client = HuggingFaceClient(
            HuggingFaceClientArgs(
                token=config.token,
                endpoint=config.endpoint,
            )
        )
        scanner = HuggingFaceScanner(client)
        return scanner

    @override
    async def execute(self, context: ImportStepContext, input_data: None) -> DownloadStepResult:
        if not context.storage_pool:
            raise ObjectStorageConfigInvalidError(
                "Storage pool not configured for import operations"
            )

        registry_config = self._registry_configs.get(context.registry_name)
        if not registry_config:
            raise RegistryNotFoundError(f"Unknown registry: {context.registry_name}")

        download_storage_name = context.storage_step_mappings.get(
            ArtifactStorageImportStep.DOWNLOAD
        )
        if not download_storage_name:
            raise StorageStepRequiredStepNotProvided(
                "No storage mapping provided for DOWNLOAD step"
            )

        chunk_size = registry_config.download_chunk_size

        log.info(f"Rescanning model for latest metadata: {context.model}")
        scanner = self._make_scanner(context.registry_name)
        file_infos = await scanner.list_model_files_info(context.model)

        file_count = len(file_infos)
        file_total_size = sum(file.size for file in file_infos)
        log.info(
            f"Found files to download: model={context.model}, file_count={file_count}, "
            f"total_size={file_total_size / (1024 * 1024)} MB"
        )

        # Initialize artifact download tracking in Redis with all file information
        revision = context.model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        file_info_list = [(file.path, file.size) for file in file_infos]
        await self._redis_client.init_artifact_download(
            model_id=context.model.model_id,
            revision=revision,
            file_info_list=file_info_list,
        )

        downloaded_files: list[tuple[FileObjectData, str]] = []
        total_bytes = 0

        for file_info in file_infos:
            storage_key = await self._download_file_to_storage(
                file_info=file_info,
                model=context.model,
                storage_name=download_storage_name,
                storage_pool=context.storage_pool,
                download_chunk_size=chunk_size,
                redis_client=self._redis_client,
                token=registry_config.token,
            )
            downloaded_files.append((file_info, storage_key))
            total_bytes += file_info.size

        log.info(
            f"Download completed: model={context.model}, files={len(downloaded_files)}, "
            f"total_bytes={total_bytes}"
        )

        return DownloadStepResult(
            downloaded_files=downloaded_files,
            storage_name=download_storage_name,
            total_bytes=total_bytes,
        )

    async def _download_file_to_storage(
        self,
        *,
        file_info: FileObjectData,
        model: ModelTarget,
        storage_name: str,
        storage_pool: AbstractStoragePool,
        download_chunk_size: int,
        redis_client: ValkeyArtifactDownloadTrackingClient,
        token: Optional[str] = None,
    ) -> str:
        """Download file from HuggingFace to specified storage"""
        storage = storage_pool.get_storage(storage_name)

        revision = model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        storage_key = f"{model.model_id}/{revision}/{file_info.path}"

        log.info(
            f"[download] Starting download to {storage_name}: file_path={file_info.path}, "
            f"storage_key={storage_key}, file_size={file_info.size}"
        )

        ctype = mimetypes.guess_type(file_info.path)[0] or "application/octet-stream"

        data_stream = HuggingFaceFileDownloadStreamReader(
            url=file_info.download_url,
            chunk_size=download_chunk_size,
            max_retries=8,
            content_type=ctype,
            redis_client=redis_client,
            model_id=model.model_id,
            revision=revision,
            file_path=file_info.path,
            token=token,
        )

        await storage.stream_upload(
            filepath=storage_key,
            data_stream=data_stream,
        )

        log.info(f"[download] Successfully downloaded to {storage_name}: {storage_key}")
        return storage_key


class HuggingFaceVerifyStep(ModelVerifyStep):
    """Step to verify downloaded files in HuggingFace model import"""

    @property
    @override
    def registry_type(self) -> ArtifactRegistryType:
        return ArtifactRegistryType.HUGGINGFACE


class HuggingFaceArchiveStep(ModelArchiveStep):
    """Step to move downloaded files to archive storage"""

    @property
    @override
    def registry_type(self) -> ArtifactRegistryType:
        return ArtifactRegistryType.HUGGINGFACE


def create_huggingface_import_pipeline(
    registry_configs: dict[str, Any],
    transfer_manager: StorageTransferManager,
    storage_step_mappings: dict[ArtifactStorageImportStep, str],
    artifact_verifier_ctx: ArtifactVerifierContext,
    event_producer: EventProducer,
    redis_client: ValkeyArtifactDownloadTrackingClient,
) -> ImportPipeline:
    """Create ImportPipeline for HuggingFace based on storage step mappings."""
    steps: list[ImportStep[Any]] = []

    # Add steps based on what's present in storage_step_mappings
    if ArtifactStorageImportStep.DOWNLOAD in storage_step_mappings:
        steps.append(HuggingFaceDownloadStep(registry_configs, redis_client))

    if ArtifactStorageImportStep.VERIFY in storage_step_mappings:
        steps.append(HuggingFaceVerifyStep(artifact_verifier_ctx, transfer_manager, event_producer))

    if ArtifactStorageImportStep.ARCHIVE in storage_step_mappings:
        steps.append(HuggingFaceArchiveStep(transfer_manager))

    return ImportPipeline(steps)
