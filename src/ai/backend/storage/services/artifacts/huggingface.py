from __future__ import annotations

import asyncio
import logging
import mimetypes
import ssl
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Callable, Final, Optional, Protocol, override

import aiohttp

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.artifact.types import ArtifactRegistryType
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
from ai.backend.storage.exception import (
    HuggingFaceAPIError,
    HuggingFaceModelNotFoundError,
    ObjectStorageConfigInvalidError,
    RegistryNotFoundError,
    StorageStepMappingNotProvidedError,
)
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
_DEFAULT_DOWNLOAD_LOGGING_INTERVAL_SECS = 15
_DEFAULT_BYTESIZE_INTERVAL = 64 * _MiB

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
    total: Optional[int]
    etag: Optional[str]
    accept_ranges: bool


class _DownloadProgressLogger(Protocol):
    def __call__(self, offset: int, final: bool = False) -> None: ...


def _make_download_progress_logger(
    *,
    total_getter: Callable[[], Optional[int]],
    bytes_interval: int = _DEFAULT_BYTESIZE_INTERVAL,
    secs_interval: float = _DEFAULT_DOWNLOAD_LOGGING_INTERVAL_SECS,
) -> _DownloadProgressLogger:
    """
    Return a lightweight progress logging callback.

    Args:
        total_getter: A callable that returns the total number of bytes to download.
        bytes_interval: The number of bytes to download before logging progress.
        secs_interval: The number of seconds to wait before logging progress.
    """

    last_t = time.monotonic()
    last_bytes = 0

    def _fmt_eta(eta_sec: Optional[float]) -> str:
        """Format ETA seconds as H:MM:SS or '?' if unknown."""
        if eta_sec is None or eta_sec >= 1e9:
            return "?"
        m, s = divmod(int(eta_sec), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}"

    def log_progress(offset: int, final: bool = False) -> None:
        nonlocal last_t, last_bytes

        now = time.monotonic()
        bytes_since = offset - last_bytes
        secs_since = now - last_t

        # Skip if neither interval threshold is met (and not final)
        if not final and bytes_since < bytes_interval and secs_since < secs_interval:
            return

        inst_mibs = (bytes_since / _MiB) / secs_since if secs_since > 0 else 0.0
        total = total_getter()

        if total:
            pct = (offset * 100.0) / total if total > 0 else 0.0
            remain = max(total - offset, 0)
            eta_sec = (remain / (inst_mibs * _MiB)) if inst_mibs > 0 else None
            eta_str = _fmt_eta(eta_sec)

            log.trace(
                "[stream_hf2b] Downloading... {:.1f}% ({:,.1f} / {:,.1f} MiB) inst={:.2f} MiB/s ETA={}".format(
                    pct, offset / _MiB, total / _MiB, inst_mibs, eta_str
                )
            )
        else:
            log.trace(
                "[stream_hf2b] Downloading... {:,.1f} MiB (total unknown) inst={:.2f} MiB/s".format(
                    offset / _MiB, inst_mibs
                )
            )

        last_t = now
        last_bytes = offset

    return log_progress


class HuggingFaceFileDownloadStreamReader(StreamReader):
    _url: str
    _chunk_size: int
    _max_retries: int
    _content_type: Optional[str]

    def __init__(
        self, url: str, chunk_size: int, max_retries: int, content_type: Optional[str]
    ) -> None:
        self._url = url
        self._chunk_size = chunk_size
        self._max_retries = max_retries
        self._content_type = content_type

    async def _probe_head(self) -> _ProbeHeadInfo:
        """
        Probe metadata via HEAD.
        - May set total size, etag, and Accept-Ranges support.
        - Any failure is swallowed (best effort).
        """
        total: Optional[int] = None
        etag: Optional[str] = None
        accept_ranges: bool = False

        headers_base = _PROBE_HEAD_BASE_HEADER
        try:
            async with self._session.head(
                self._url, headers=headers_base, allow_redirects=True
            ) as resp:
                content_length = resp.headers.get("Content-Length")
                if content_length and content_length.isdigit():
                    total = int(content_length)

                new_etag = resp.headers.get("ETag")
                if etag and new_etag and new_etag != etag:
                    raise aiohttp.ClientPayloadError("ETag changed on HEAD")
                etag = etag or new_etag
                accept_ranges = "bytes" in (resp.headers.get("Accept-Ranges", "")).lower()
        except Exception:
            # HEAD is best-effort; ignore failures.
            pass

        return _ProbeHeadInfo(total=total, etag=etag, accept_ranges=accept_ranges)

    @override
    async def read(self) -> AsyncIterator[bytes]:
        """
        Stream bytes from `url`.
        """
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None, sock_read=None),
            auto_decompress=False,
        )

        headers_base = _PROBE_HEAD_BASE_HEADER
        progress_logger = _make_download_progress_logger(
            total_getter=lambda: total,
        )

        offset = 0
        backoff = 1.0
        retries = 0

        total: Optional[int] = None
        etag: Optional[str] = None
        accept_ranges = False

        try:
            probe_info = await self._probe_head()
            total = probe_info.total
            etag = probe_info.etag
            accept_ranges = probe_info.accept_ranges

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

                        # Fill total size from response headers if still unknown
                        if total is None:
                            if resp.status == 200:
                                content_length = resp.headers.get("Content-Length")
                                if content_length and content_length.isdigit():
                                    total = int(content_length)
                            elif resp.status == 206:
                                content_range = resp.headers.get(
                                    "Content-Range"
                                )  # e.g. "bytes 123-456/789"
                                if content_range and "/" in content_range:
                                    try:
                                        total = int(content_range.split("/")[-1])
                                    except ValueError:
                                        pass
                            # TODO: Handle else case

                        async for chunk in resp.content.iter_chunked(self._chunk_size):
                            if not chunk:
                                continue
                            offset += len(chunk)
                            progress_logger(offset)
                            yield chunk

                    # total unknown
                    if total is None:
                        progress_logger(offset, final=True)
                        log.warning("Skipped download of %s since total size is unknown", self._url)
                        break

                    # Completed
                    if offset >= total:
                        progress_logger(offset, final=True)
                        break

                    # Unexpected early EOF → retry
                    raise aiohttp.ClientPayloadError("Early EOF before Content-Length")

                except _DOWNLOAD_RETRIABLE_ERROR as e:
                    retries += 1
                    if retries > self._max_retries:
                        progress_logger(offset, final=True)
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
        finally:
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


class HuggingFaceService:
    """Service for HuggingFace model operations"""

    _storage_pool: StoragePool
    _background_task_manager: BackgroundTaskManager
    _registry_configs: dict[str, HuggingfaceConfig]
    _event_producer: EventProducer
    _transfer_manager: StorageTransferManager

    def __init__(self, args: HuggingFaceServiceArgs):
        self._storage_pool = args.storage_pool
        self._background_task_manager = args.background_task_manager
        self._registry_configs = args.registry_configs
        self._event_producer = args.event_producer
        self._transfer_manager = StorageTransferManager(args.storage_pool)

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

    async def scan_models_sync(
        self,
        registry_name: str,
        limit: int,
        sort: ModelSortKey,
        search: Optional[str] = None,
    ) -> list[ModelData]:
        """List HuggingFace models with metadata including README content synchronously.

        This method waits for all metadata (including README) to be fully downloaded before returning.

        Args:
            registry_name: Name of the HuggingFace registry
            limit: Maximum number of models to retrieve
            search: Search query to filter models
            sort: Sort criteria ("downloads", "likes", "created_at", "last_modified")

        Returns:
            List of models with complete metadata including README content

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        log.info(
            f"Scanning HuggingFace models synchronously: limit={limit}, search={search}, sort={sort}"
        )

        scanner = self._make_scanner(registry_name)
        models = await scanner.scan_models(limit=limit, search=search, sort=sort)

        # Download metadata synchronously and update models with README content
        if models:
            await scanner.download_metadata_batch_sync(models)

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
        # Create import context
        context = ImportStepContext(
            model=model,
            registry_name=registry_name,
            storage_pool=self._storage_pool,
            progress_reporter=None,  # Not needed for single model import
            storage_step_mappings=storage_step_mappings,
            step_metadata={},
        )

        try:
            # Execute import pipeline
            await pipeline.execute(context)

            log.info(f"Model import completed: {model}")

            await self._event_producer.anycast_event(
                ModelImportDoneEvent(
                    model_id=model.model_id,
                    revision=model.resolve_revision(ArtifactRegistryType.HUGGINGFACE),
                    registry_name=registry_name,
                    registry_type=ArtifactRegistryType.HUGGINGFACE,
                )
            )

        except HuggingFaceModelNotFoundError:
            raise
        except Exception as e:
            raise HuggingFaceAPIError(f"Import failed for {model}: {str(e)}") from e

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

                        # TODO: Batch import logic can be optimized further
                        # Create import context for batch processing
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

    async def _import_with_step_mappings(
        self,
        *,
        model: ModelTarget,
        file_infos: list[FileObjectData],
        download_chunk_size: int,
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
    ) -> tuple[int, int]:
        """Import files through multiple stages (download -> archive).

        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        successful_uploads = 0
        failed_uploads = 0

        for file_info in file_infos:
            try:
                await self._import_single_file_with_step_mappings(
                    file_info=file_info,
                    model=model,
                    download_chunk_size=download_chunk_size,
                    storage_step_mappings=storage_step_mappings,
                )
                successful_uploads += 1
            except Exception as e:
                log.error(
                    f"Failed to import file through stages: {str(e)}, {model}, file_path={file_info.path}"
                )
                failed_uploads += 1

        return successful_uploads, failed_uploads

    async def _import_single_file_with_step_mappings(
        self,
        *,
        file_info: FileObjectData,
        model: ModelTarget,
        download_chunk_size: int,
        storage_step_mappings: dict[ArtifactStorageImportStep, str],
    ) -> None:
        """Import a single file through download -> archive stages."""
        if not self._storage_pool:
            raise ObjectStorageConfigInvalidError(
                "Storage pool not configured for import operations"
            )

        revision = model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        storage_key = f"{model.model_id}/{revision}/{file_info.path}"

        # Get storage for each step from mappings
        download_storage_name = storage_step_mappings.get(ArtifactStorageImportStep.DOWNLOAD)
        archive_storage_name = storage_step_mappings.get(ArtifactStorageImportStep.ARCHIVE)

        if not download_storage_name:
            raise StorageStepMappingNotProvidedError(
                "No storage mapping provided for DOWNLOAD step"
            )
        if not archive_storage_name:
            raise StorageStepMappingNotProvidedError("No storage mapping provided for ARCHIVE step")

        try:
            # Stage 1: Download to download storage
            await self._download_to_storage(
                file_info=file_info,
                storage_key=storage_key,
                storage_name=download_storage_name,
                download_chunk_size=download_chunk_size,
            )

            # Stage 2: Transfer to archive storage (if different)
            if archive_storage_name != download_storage_name:
                await self._transfer_manager.transfer_file(
                    source_storage_name=download_storage_name,
                    dest_storage_name=archive_storage_name,
                    source_path=storage_key,
                    dest_path=storage_key,
                )

            log.info(
                f"Successfully imported file through all stages: {model}, file_path={file_info.path}, "
                f"download={download_storage_name}, archive={archive_storage_name}"
            )

        except Exception as e:
            # Cleanup on failure
            await self._cleanup_failed_import(
                storage_key=storage_key,
                storages=[download_storage_name, archive_storage_name],
            )
            raise HuggingFaceAPIError(
                f"Failed to import file through stages {file_info.path}: {str(e)}"
            ) from e

    async def _download_to_storage(
        self,
        *,
        file_info: FileObjectData,
        storage_key: str,
        storage_name: str,
        download_chunk_size: int,
    ) -> None:
        """Download file from HuggingFace to specified storage."""
        storage = self._storage_pool.get_storage(storage_name)

        log.info(
            f"[download] Starting download to {storage_name}: file_path={file_info.path}, "
            f"storage_key={storage_key}, file_size={file_info.size}"
        )

        ctype = mimetypes.guess_type(file_info.path)[0] or "application/octet-stream"

        data_stream = HuggingFaceFileDownloadStreamReader(
            url=file_info.download_url,
            chunk_size=download_chunk_size,
            max_retries=8,  # TODO: Add config
            content_type=ctype,
        )

        await storage.stream_upload(
            filepath=storage_key,
            data_stream=data_stream,
        )

        log.info(f"[download] Successfully downloaded to {storage_name}: {storage_key}")

    async def _cleanup_failed_import(
        self,
        *,
        storage_key: str,
        storages: list[str],
    ) -> None:
        """Cleanup files from storages on failed import."""
        for storage_name in set(storages):  # Remove duplicates
            try:
                storage = self._storage_pool.get_storage(storage_name)
                await storage.delete_object(storage_key)
                log.info(f"[cleanup] Removed failed import file: {storage_name}:{storage_key}")
            except Exception as e:
                log.warning(
                    f"[cleanup] Failed to cleanup file: {storage_name}:{storage_key}: {str(e)}"
                )


# Import Pipeline Steps


class HuggingFaceDownloadStep(ImportStep[None]):
    """Step to download files from HuggingFace"""

    def __init__(self, registry_configs: dict[str, HuggingfaceConfig]) -> None:
        self._registry_configs = registry_configs

    @property
    def step_type(self) -> ArtifactStorageImportStep:
        return ArtifactStorageImportStep.DOWNLOAD

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
            raise StorageStepMappingNotProvidedError(
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

        downloaded_files: list[tuple[FileObjectData, str]] = []
        total_bytes = 0

        for file_info in file_infos:
            storage_key = await self._download_file_to_storage(
                file_info=file_info,
                model=context.model,
                storage_name=download_storage_name,
                storage_pool=context.storage_pool,
                download_chunk_size=chunk_size,
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
        storage_pool: StoragePool,
        download_chunk_size: int,
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
        )

        await storage.stream_upload(
            filepath=storage_key,
            data_stream=data_stream,
        )

        log.info(f"[download] Successfully downloaded to {storage_name}: {storage_key}")
        return storage_key

    @override
    async def cleanup_on_failure(self, context: ImportStepContext) -> None:
        """Clean up failed files from download storage"""
        download_storage_name = context.storage_step_mappings.get(
            ArtifactStorageImportStep.DOWNLOAD
        )
        if not download_storage_name:
            return

        revision = context.model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        model_prefix = f"{context.model.model_id}/{revision}"

        try:
            storage = context.storage_pool.get_storage(download_storage_name)
            await storage.delete_object(model_prefix)
            log.info(f"[cleanup] Removed failed download: {download_storage_name}:{model_prefix}")
        except Exception as e:
            log.warning(
                f"[cleanup] Failed to cleanup download: {download_storage_name}:{model_prefix}: {str(e)}"
            )


class HuggingFaceArchiveStep(ImportStep[DownloadStepResult]):
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
            raise StorageStepMappingNotProvidedError("No storage mapping provided for ARCHIVE step")

        # No need to move if download and archive storage are the same
        if download_storage == archive_storage:
            log.info(
                f"Archive step skipped - download and archive storage are the same: {archive_storage}"
            )
            return

        log.info(
            f"Starting archive transfer: {download_storage} -> {archive_storage}, "
            f"files={len(input_data.downloaded_files)}"
        )

        # Move each file from download storage to archive storage
        for file_info, storage_key in input_data.downloaded_files:
            try:
                await self._transfer_manager.transfer_file(
                    source_storage_name=download_storage,
                    dest_storage_name=archive_storage,
                    source_path=storage_key,
                    dest_path=storage_key,
                )
                log.debug(f"Transferred file to archive: {storage_key}")
            except Exception as e:
                log.error(f"Failed to transfer file to archive: {storage_key}: {str(e)}")
                raise

        log.info(
            f"Archive transfer completed: {download_storage} -> {archive_storage}, "
            f"files={len(input_data.downloaded_files)}"
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
            await storage.delete_object(model_prefix)
            log.info(f"[cleanup] Removed failed archive: {archive_storage}:{model_prefix}")
        except Exception as e:
            log.warning(
                f"[cleanup] Failed to cleanup archive: {archive_storage}:{model_prefix}: {str(e)}"
            )
