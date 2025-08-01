"""HuggingFace model scanner implementation for Backend.AI storage."""

import logging
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import aiohttp

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.storage.registries.types import FileInfo, ModelInfo
from ai.backend.common.dto.storage.request import ObjectStorageOperationType, ObjectStorageTokenData
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.client.huggingface import HuggingFaceScanner
from ai.backend.storage.exception import (
    HuggingFaceAPIError,
    HuggingFaceModelNotFoundError,
)
from ai.backend.storage.services.storages import StoragesService

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_CHUNK_SIZE = 8192  # Default chunk size for streaming downloads
_DEFAULT_EXPIRATION = 3600  # Default expiration time for storage tokens (1 hour)


@dataclass
class HuggingFaceServiceArgs:
    scanner: HuggingFaceScanner
    background_task_manager: BackgroundTaskManager
    storage_service: StoragesService


class HuggingFaceService:
    """Service for HuggingFace model operations"""

    _scanner: HuggingFaceScanner
    _storages_service: StoragesService
    _background_task_manager: BackgroundTaskManager

    def __init__(self, args: HuggingFaceServiceArgs):
        self._scanner = args.scanner
        self._storages_service = args.storage_service
        self._background_task_manager = args.background_task_manager

    async def list_models(
        self, limit: int = 10, search: Optional[str] = None, sort: str = "downloads"
    ) -> list[ModelInfo]:
        """List HuggingFace models with metadata.

        Args:
            limit: Maximum number of models to retrieve
            search: Search query to filter models
            sort: Sort criteria ("downloads", "likes", "created", "modified")

        Returns:
            List of ModelInfo objects

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Listing HuggingFace models: limit={limit}, search={search}, sort={sort}")
        return await self._scanner.scan_models(limit=limit, search=search, sort=sort)

    async def get_model(self, model_id: str) -> ModelInfo:
        """Get detailed information about a specific model.

        Args:
            model_id: HuggingFace model ID

        Returns:
            ModelInfo object with complete metadata

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Getting HuggingFace model details: model_id={model_id}")
        return await self._scanner.scan_model(model_id)

    async def list_model_files(self, model_id: str) -> list[FileInfo]:
        """List all files in a specific model.

        Args:
            model_id: HuggingFace model ID

        Returns:
            List of FileInfo objects

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        log.info(f"Listing model files: model_id={model_id}")
        model = await self._scanner.scan_model(model_id)
        return model.files

    async def get_download_url(self, model_id: str, filename: str) -> str:
        """Get download URL for a specific file.

        Args:
            model_id: HuggingFace model ID
            filename: File name within the model

        Returns:
            Download URL string
        """
        log.info(f"Getting download URL: model_id={model_id}, filename={filename}")
        return self._scanner.get_download_url(model_id, filename)

    async def _download_file_stream(self, url: str, timeout: int = 300) -> AsyncIterator[bytes]:
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
        self, file_info: FileInfo, model_id: str, storage_name: str, bucket_name: str
    ) -> bool:
        """Upload a single model file to storage.

        Args:
            file_info: File information with download URL
            model_id: HuggingFace model ID
            storage_name: Target storage name
            bucket_name: Target bucket name

        Returns:
            True if upload successful, False otherwise
        """
        if not self._storages_service:
            raise HuggingFaceAPIError("Storage service not configured for import operations")

        try:
            # Create storage key path: {model_id}/{file_path}
            storage_key = f"{model_id}/{file_info.path}"

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
                f"Starting file upload: model_id={model_id}, file_path={file_info.path}, "
                f"storage_key={storage_key}, file_size={file_info.size}"
            )

            # Download from HuggingFace and stream directly to storage
            download_stream = self._download_file_stream(file_info.download_url)

            # Upload to storage using existing service
            upload_result = await self._storages_service.stream_upload(
                storage_name=storage_name,
                bucket_name=bucket_name,
                token_data=token_data,
                data_stream=download_stream,
            )

            if upload_result.success:
                log.info(
                    f"Successfully uploaded file: model_id={model_id}, file_path={file_info.path}, "
                    f"storage_key={storage_key}"
                )
                return True
            else:
                log.error(
                    f"Upload failed: model_id={model_id}, file_path={file_info.path}, "
                    f"storage_key={storage_key}"
                )
                return False

        except Exception as e:
            log.error(
                f"Failed to upload file: {str(e)}, model_id={model_id}, file_path={file_info.path}"
            )
            return False

    async def import_model(self, model_id: str, storage_name: str, bucket_name: str) -> uuid.UUID:
        """Import a HuggingFace model to storage.

        Args:
            model_id: HuggingFace model ID to import
            storage_name: Target storage name
            bucket_name: Target bucket name
            rescan: Whether to rescan the model before importing

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """

        async def _import_model(reporter: ProgressReporter) -> None:
            try:
                # Step 1: Get model metadata (rescan if requested)
                log.info(f"Rescanning model for latest metadata: model_id={model_id}")
                model_info = await self._scanner.scan_model(model_id)

                if not model_info.files:
                    log.warning(f"No files found in model: model_id={model_id}")
                    return

                log.info(
                    f"Found files to import: model_id={model_id}, file_count={len(model_info.files)}, "
                    f"total_size_mb={sum(f.size for f in model_info.files) / (1024 * 1024)}"
                )

                # Step 2: Import all model files
                successful_uploads = 0
                failed_uploads = 0

                for file_info in model_info.files:
                    try:
                        success = await self._upload_model_file(
                            file_info=file_info,
                            model_id=model_id,
                            storage_name=storage_name,
                            bucket_name=bucket_name,
                        )

                        if success:
                            successful_uploads += 1
                        else:
                            failed_uploads += 1

                    except Exception as e:
                        log.error(
                            f"Failed to upload file: {str(e)}, model_id={model_id}, file_path={file_info.path}"
                        )
                        failed_uploads += 1

                # Step 3: Log final results
                log.info(
                    f"Model import completed: model_id={model_id}, successful_uploads={successful_uploads}, "
                    f"failed_uploads={failed_uploads}, total_files={len(model_info.files)}"
                )

                if failed_uploads > 0:
                    log.warning(
                        f"Some files failed to import: model_id={model_id}, failed_count={failed_uploads}"
                    )
            except HuggingFaceModelNotFoundError:
                log.error(f"Model not found: model_id={model_id}")
                raise
            except Exception as e:
                log.error(f"Model import failed: error={str(e)}, model_id={model_id}")
                raise HuggingFaceAPIError(f"Import failed for {model_id}: {str(e)}") from e

        bgtask_id = await self._background_task_manager.start(_import_model)
        return bgtask_id

    async def import_models_batch(
        self, model_ids: list[str], storage_name: str, bucket_name: str
    ) -> uuid.UUID:
        """Import multiple HuggingFace models to storage in batch.

        Args:
            model_ids: List of HuggingFace model IDs to import
            storage_name: Target storage name
            bucket_name: Target bucket name
            rescan: Whether to rescan the models before importing

        Raises:
            HuggingFaceAPIError: If API call fails
        """

        async def _import_models_batch(reporter: ProgressReporter) -> None:
            log.info(
                f"Starting batch model import: model_count={len(model_ids)}, "
                f"storage_name={storage_name}, bucket_name={bucket_name}"
            )

            if not model_ids:
                log.warning("No models to import")
                return

            try:
                successful_models = 0
                failed_models = 0

                # Process each model sequentially to avoid overwhelming the system
                # In a production system, this could be enhanced with parallel processing
                # and proper job queue management
                for i, model_id in enumerate(model_ids, 1):
                    try:
                        log.info(
                            f"Processing model in batch: model_id={model_id}, progress={i}/{len(model_ids)}"
                        )

                        # Import individual model
                        await self.import_model(
                            model_id=model_id,
                            storage_name=storage_name,
                            bucket_name=bucket_name,
                        )

                        successful_models += 1
                        log.info(
                            f"Successfully imported model in batch: model_id={model_id}, progress={i}/{len(model_ids)}"
                        )

                    except HuggingFaceModelNotFoundError:
                        failed_models += 1
                        log.error(
                            f"Model not found in batch import: model_id={model_id}, progress={i}/{len(model_ids)}"
                        )

                    except Exception as e:
                        failed_models += 1
                        log.error(
                            f"Failed to import model in batch: {str(e)}, model_id={model_id}, progress={i}/{len(model_ids)}"
                        )

                # Log final batch results
                log.info(
                    f"Batch model import completed: total_models={len(model_ids)}, "
                    f"successful_models={successful_models}, failed_models={failed_models}"
                )

                if failed_models > 0:
                    log.warning(
                        f"Some models failed to import in batch: failed_count={failed_models}"
                    )
            except Exception as e:
                log.error(f"Batch model import failed: {str(e)}")
                raise HuggingFaceAPIError(f"Batch import failed: {str(e)}") from e

        bgtask_id = await self._background_task_manager.start(_import_models_batch)
        return bgtask_id
