"""HuggingFace client implementation for Backend.AI storage."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from huggingface_hub import HfApi, hf_hub_url, list_models, list_repo_files, model_info
from huggingface_hub.hf_api import ModelInfo as HfModelInfo
from huggingface_hub.hf_api import RepoFile, RepoFolder

from ai.backend.common.data.storage.registries.types import FileInfo, ModelInfo
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import HuggingFaceAPIError, HuggingFaceModelNotFoundError

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class HuggingFaceClientArgs:
    token: Optional[str]
    endpoint: Optional[str]


class HuggingFaceClient:
    """Client for HuggingFace Hub API operations."""

    _token: Optional[str]
    _endpoint: Optional[str]
    _api: HfApi

    def __init__(self, args: HuggingFaceClientArgs):
        """Initialize HuggingFace client.

        Args:
            args: Client configuration arguments
        """
        self._token = args.token
        self._endpoint = args.endpoint
        self._api = HfApi(token=args.token, endpoint=args.endpoint)

    async def scan_models(
        self, search: Optional[str] = None, sort: str = "downloads", limit: int = 10
    ) -> list[HfModelInfo]:
        """List models from HuggingFace Hub.

        Args:
            search: Search query to filter models
            sort: Sort criteria ("downloads", "likes", "created", "modified")
            limit: Maximum number of models to retrieve

        Returns:
            List of HfModelInfo objects

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        try:
            models = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list_models(
                    search=search,
                    sort=sort,
                    direction=-1,  # Descending order
                    limit=limit,
                    token=self._token,
                ),
            )
            return list(models)
        except Exception as e:
            log.error(f"Failed to list models: {str(e)}")
            raise HuggingFaceAPIError(f"Failed to list models: {str(e)}") from e

    async def scan_model(self, model_id: str) -> HfModelInfo:
        """Get detailed information about a specific model.

        Args:
            model_id: HuggingFace model ID

        Returns:
            HfModelInfo object with model metadata

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        try:
            model = await asyncio.get_event_loop().run_in_executor(
                None, lambda: model_info(model_id, token=self._token)
            )
            return model
        except Exception as e:
            if "not found" in str(e).lower():
                raise HuggingFaceModelNotFoundError(f"Model not found: {model_id}") from e
            log.error(f"Failed to get model info for {model_id}: {str(e)}")
            raise HuggingFaceAPIError(f"Failed to get model info for {model_id}: {str(e)}") from e

    async def list_model_filepaths(self, model_id: str) -> list[str]:
        """List files in a model repository.

        Args:
            model_id: HuggingFace model ID

        Returns:
            List of file paths

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        try:
            files = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list_repo_files(model_id, token=self._token)
            )
            return files
        except Exception as e:
            log.error(f"Failed to list files for {model_id}: {str(e)}")
            raise HuggingFaceAPIError(f"Failed to list files for {model_id}: {str(e)}") from e

    async def list_model_files_info(
        self, model_id: str, paths: list[str]
    ) -> list[RepoFile | RepoFolder]:
        """Get information about specific paths in a repository.

        Args:
            model_id: HuggingFace model ID
            paths: List of file paths to get info for

        Returns:
            Path information from HfApi

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._api.get_paths_info(model_id, paths=paths, repo_type="model"),
            )
            return info
        except Exception as e:
            log.error(f"Failed to get paths info for {model_id} ({paths}): {str(e)}")
            raise HuggingFaceAPIError(f'Failed to get paths info for "{model_id}": {str(e)}') from e

    def get_download_url(self, model_id: str, filename: str) -> str:
        """Generate download URL for a specific file.

        Args:
            model_id: HuggingFace model ID
            filename: File name

        Returns:
            Download URL
        """
        try:
            return hf_hub_url(repo_id=model_id, filename=filename)
        except Exception:
            # Fallback URL
            return f"https://huggingface.co/{model_id}/resolve/main/{filename}"


@dataclass
class HuggingFaceScannerArgs:
    client: HuggingFaceClient


class HuggingFaceScanner:
    """Scanner for HuggingFace models and metadata."""

    _client: HuggingFaceClient

    def __init__(self, client: HuggingFaceClient):
        """Initialize HuggingFace scanner.

        Args:
            client: HuggingFaceClient instance for API calls
        """
        self._client = client

    async def scan_models(
        self,
        limit: int = 10,
        search: Optional[str] = None,
        sort: str = "downloads",
    ) -> list[ModelInfo]:
        """Scan HuggingFace models and retrieve metadata.

        Args:
            limit: Maximum number of models to retrieve
            search: Search query to filter models
            sort: Sort criteria ("downloads", "likes", "created", "modified")

        Returns:
            List of ModelInfo objects containing model metadata

        Raises:
            HuggingFaceAPIError: If API call fails
        """
        try:
            log.info(f"Scanning HuggingFace models: limit={limit}, search={search}, sort={sort}")
            models = await self._client.scan_models(search=search, sort=sort, limit=limit)

            model_infos: list[ModelInfo] = []
            for model in models:
                try:
                    model_infos.append(
                        ModelInfo(
                            id=model.id,
                            name=model.id.split("/")[-1],
                            author=model.author,
                            tags=model.tags or [],
                            created_at=model.created_at,
                            last_modified=model.last_modified,
                        )
                    )
                except Exception as e:
                    log.warning(
                        f"Failed to get details for model: model_id={model.id}, error={str(e)}"
                    )
                    continue

            log.info(f"Successfully scanned HuggingFace models: count={len(model_infos)}")
            return model_infos

        except Exception as e:
            log.error(f"Failed to scan HuggingFace models: {str(e)}")
            raise HuggingFaceAPIError(f"Failed to scan models: {str(e)}") from e

    async def scan_model(self, model_id: str) -> ModelInfo:
        """Scan a specific model by ID.

        Args:
            model_id: HuggingFace model ID (e.g., "microsoft/DialoGPT-medium")

        Returns:
            ModelInfo object with model metadata and files

        Raises:
            HuggingFaceModelNotFoundError: If model is not found
            HuggingFaceAPIError: If API call fails
        """
        try:
            log.info(f"Scanning specific HuggingFace model: model_id={model_id}")
            model = await self._client.scan_model(model_id)

            result = ModelInfo(
                id=model_id,
                name=model_id.split("/")[-1],
                author=model.author,
                tags=model.tags or [],
                created_at=model.created_at,
                last_modified=model.last_modified,
            )

            log.info(
                f"Successfully scanned HuggingFace model: model_id={model_id}",
            )
            return result

        except Exception as e:
            log.error(f"Failed to scan HuggingFace model {model_id}: {str(e)}")
            if "not found" in str(e).lower():
                raise HuggingFaceModelNotFoundError(f"Model not found: {model_id}") from e
            raise HuggingFaceAPIError(f"Failed to scan model {model_id}: {str(e)}") from e

    def get_download_url(self, model_id: str, filename: str) -> str:
        """Generate download URL for a specific file.

        Args:
            model_id: HuggingFace model ID
            filename: File name

        Returns:
            Download URL
        """
        return self._client.get_download_url(model_id, filename)

    async def list_model_files_info(self, model_id: str) -> list[FileInfo]:
        """Get model file information list as FileInfo objects.

        Args:
            model_id: Model ID

        Returns:
            List of FileInfo objects
        """
        try:
            filepaths = await self._client.list_model_filepaths(model_id)
            model_files = await self._client.list_model_files_info(model_id, filepaths)
            file_infos = []

            for file in model_files:
                try:
                    match file:
                        case RepoFile():
                            file_obj = FileInfo(
                                path=file.path,
                                size=file.size,
                                type="file",
                                download_url=self._client.get_download_url(model_id, file.path),
                            )
                        case RepoFolder():
                            file_obj = FileInfo(
                                path=file.path,
                                size=0,
                                type="directory",
                                download_url=self._client.get_download_url(model_id, file.path),
                            )
                        case _:
                            log.error(f"Unknown file type for {file}, skipping...")
                            continue
                    file_infos.append(file_obj)

                except Exception as e:
                    path = getattr(file, "path", "unknown")
                    log.error(
                        f"Error processing file {path} info for model {model_id}. Details: {str(e)}"
                    )

            return file_infos

        except Exception as e:
            log.error(f"Error getting file list for {model_id}: {str(e)}")
            return []
