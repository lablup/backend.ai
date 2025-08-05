"""HuggingFace model scanner implementation for Backend.AI storage."""

import logging
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import aiohttp

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.storage.registries.types import FileInfo, ModelInfo, ModelTarget
from ai.backend.common.dto.storage.request import ObjectStorageOperationType, ObjectStorageTokenData
from ai.backend.common.types import DispatchResult
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
    RegistryNotFoundError,
)
from ai.backend.storage.services.storages import StoragesService

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_CHUNK_SIZE = 8192  # Default chunk size for streaming downloads
_DEFAULT_EXPIRATION = 3600  # Default expiration time for storage tokens (1 hour)
_DEFAULT_FILE_DOWNLOAD_TIMEOUT = 300  # Default timeout for file downloads in seconds


@dataclass
class HuggingFaceServiceArgs:
    registry_configs: dict[str, HuggingfaceConfig]
    background_task_manager: BackgroundTaskManager
    storage_service: StoragesService


class HuggingFaceService:
    """Service for HuggingFace model operations"""

    _storages_service: StoragesService
    _background_task_manager: BackgroundTaskManager
    _registry_configs: dict[str, HuggingfaceConfig]

    def __init__(self, args: HuggingFaceServiceArgs):
        self._storages_service = args.storage_service
        self._background_task_manager = args.background_task_manager
        self._registry_configs = args.registry_configs

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
        search: Optional[str] = None,
        sort: str = "downloads",
    ) -> list[ModelInfo]:
        """List HuggingFace models with metadata.

        Args:
            registry_name: Name of the HuggingFace registry
            limit: Maximum number of models to retrieve
            search: Search query to filter models
            sort: Sort criteria ("downloads", "likes", "created", "modified")

        Returns:
            UUID of the background task that will perform the scan

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Scanning HuggingFace models: limit={limit}, search={search}, sort={sort}")

        models = await self._make_scanner(registry_name).scan_models(
            limit=limit, search=search, sort=sort
        )

        return models

    async def scan_model(self, registry_name: str, model: ModelTarget) -> ModelInfo:
        """Get detailed information about a specific model.

        Args:
            registry_name: Name of the HuggingFace registry
            model: ModelTarget containing model_id and revision

        Returns:
            ModelInfo object with complete metadata

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Scanning HuggingFace model: model_id={model.model_id}@{model.revision}")
        return await self._make_scanner(registry_name).scan_model(model)

    async def list_model_files(self, registry_name: str, model: ModelTarget) -> list[FileInfo]:
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
        log.info(f"Listing model files: model_id={model.model_id}@{model.revision}")
        return await self._make_scanner(registry_name).list_model_files_info(model)

    async def get_download_url(self, registry_name: str, model: ModelTarget, filename: str) -> str:
        """Get download URL for a specific file.

        Args:
            registry_name: Name of the HuggingFace registry
            model: ModelTarget containing model_id and revision
            filename: File name within the model

        Returns:
            Download URL string
        """
        log.info(
            f"Getting download URL: model_id={model.model_id}@{model.revision}, filename={filename}"
        )
        return self._make_scanner(registry_name).get_download_url(model, filename)

    async def import_model(
        self,
        registry_name: str,
        model: ModelTarget,
        storage_name: str,
        bucket_name: str,
    ) -> uuid.UUID:
        """Import a HuggingFace model to storage.

        Args:
            registry_name: Name of the HuggingFace registry
            model: HuggingFace model to import
            storage_name: Target storage name
            bucket_name: Target bucket name

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """

        async def _import_model(reporter: ProgressReporter) -> None:
            model_id = model.model_id
            revision = model.revision
            try:
                log.info(f"Rescanning model for latest metadata: model_id={model_id}@{revision}")
                scanner = self._make_scanner(registry_name)
                file_infos = await scanner.list_model_files_info(model)

                file_count = len(file_infos)
                reporter.total_progress = file_count
                file_total_size = sum(file.size for file in file_infos)
                log.info(
                    f"Found files to import: model_id={model_id}@{revision}, file_count={file_count}, "
                    f"total_size={file_total_size / (1024 * 1024)} MB"
                )

                successful_uploads = 0
                failed_uploads = 0

                for file_info in file_infos:
                    try:
                        success = await self._upload_model_file(
                            file_info=file_info,
                            model_id=model_id,
                            revision=revision,
                            storage_name=storage_name,
                            bucket_name=bucket_name,
                        )

                        if success:
                            successful_uploads += 1
                        else:
                            failed_uploads += 1

                    except Exception as e:
                        log.error(
                            f"Failed to upload file: {str(e)}, model_id={model_id}@{revision}, file_path={file_info.path}"
                        )
                        failed_uploads += 1
                    finally:
                        await reporter.update(
                            1,
                            message=f"Uploaded file: {file_info.path} to {storage_name} (bucket: {bucket_name})",
                        )

                log.info(
                    f"Model import completed: model_id={model_id}@{revision}, successful_uploads={successful_uploads}, "
                    f"failed_uploads={failed_uploads}, total_files={len(file_infos)}"
                )

                if failed_uploads > 0:
                    log.warning(
                        f"Some files failed to import: model_id={model_id}@{revision}, failed_count={failed_uploads}"
                    )
            except HuggingFaceModelNotFoundError:
                log.error(f"Model not found: model_id={model_id}@{revision}")
                raise
            except Exception as e:
                log.error(f"Model import failed: error={str(e)}, model_id={model_id}@{revision}")
                raise HuggingFaceAPIError(
                    f"Import failed for {model_id}@{revision}: {str(e)}"
                ) from e

        bgtask_id = await self._background_task_manager.start(_import_model)
        return bgtask_id

    async def import_models_batch(
        self,
        registry_name: str,
        models: list[ModelTarget],
        storage_name: str,
        bucket_name: str,
    ) -> uuid.UUID:
        """Import multiple HuggingFace models to storage in batch.

        Args:
            registry_name: Name of the HuggingFace registry
            model_ids: List of HuggingFace model IDs to import
            storage_name: Target storage name
            bucket_name: Target bucket name

        Raises:
            HuggingFaceAPIError: If API call fails
        """

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

    async def _make_download_file_stream(
        self, url: str, timeout: int = _DEFAULT_FILE_DOWNLOAD_TIMEOUT
    ) -> AsyncIterator[bytes]:
        """Download file from URL as async byte stream.

        Args:
            url: URL to download from
            timeout: Request timeout in seconds

        Yields:
            Chunks of file data as bytes

        Raises:
            HuggingFaceAPIError: If download fails
        """
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise HuggingFaceAPIError(
                            f"Download failed with status {response.status}: {url}"
                        )

                    async for chunk in response.content.iter_chunked(_DEFAULT_CHUNK_SIZE):
                        yield chunk
        except aiohttp.ClientError as e:
            raise HuggingFaceAPIError(f"HTTP client error downloading {url}: {str(e)}") from e
        except Exception as e:
            raise HuggingFaceAPIError(f"Unexpected error downloading {url}: {str(e)}") from e

    async def _upload_model_file(
        self, file_info: FileInfo, model_id: str, revision: str, storage_name: str, bucket_name: str
    ) -> bool:
        """Upload a single model file to storage.

        Args:
            file_info: File information with download URL
            model_id: HuggingFace model ID
            revision: Git revision (branch, tag, or commit hash)
            storage_name: Target storage name
            bucket_name: Target bucket name

        Returns:
            True if upload successful, False otherwise
        """
        if not self._storages_service:
            raise HuggingFaceAPIError("Storage service not configured for import operations")

        try:
            # Create storage key path: {model_id}/{revision}/{file_path}
            storage_key = f"{model_id}/{revision}/{file_info.path}"

            # Create token data for the upload
            token_data = ObjectStorageTokenData(
                op=ObjectStorageOperationType.UPLOAD,
                bucket=bucket_name,
                key=storage_key,
                expiration=_DEFAULT_EXPIRATION,
                content_type="application/octet-stream",
                filename=file_info.path.split("/")[-1],  # Extract filename
            )

            log.debug(
                f"Starting file upload to {storage_name}: model_id={model_id}@{revision}, file_path={file_info.path}, "
                f"storage_key={storage_key}, file_size={file_info.size}"
            )

            # Download from HuggingFace and stream directly to storage
            download_stream = self._make_download_file_stream(file_info.download_url)

            # Upload to storage using existing service
            upload_result = await self._storages_service.stream_upload(
                storage_name=storage_name,
                bucket_name=bucket_name,
                token_data=token_data,
                data_stream=download_stream,
            )

            if upload_result.success:
                log.info(
                    f"Successfully uploaded file to {storage_name}: model_id={model_id}@{revision}, file_path={file_info.path}, "
                    f"storage_key={storage_key}"
                )
                return True
            else:
                log.error(
                    f"Upload failed: model_id={model_id}@{revision}, file_path={file_info.path}, "
                    f"storage_key={storage_key}"
                )
                return False

        except Exception as e:
            log.error(
                f"Failed to upload file: {str(e)}, model_id={model_id}@{revision}, file_path={file_info.path}"
            )
            return False
