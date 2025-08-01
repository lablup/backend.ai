"""HuggingFace client implementation for Backend.AI storage."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

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


class HuggingFaceClient:
    """Client for HuggingFace Hub API operations."""

    _token: Optional[str]
    _api: HfApi

    def __init__(self, args: HuggingFaceClientArgs):
        """Initialize HuggingFace client.

        Args:
            args: Client configuration arguments
        """
        self._token = args.token
        self._api = HfApi(token=args.token)

    async def list_models(
        self, search: Optional[str] = None, sort: str = "downloads", limit: int = 10
    ) -> List[HfModelInfo]:
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

    async def get_model_info(self, model_id: str) -> HfModelInfo:
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

    async def list_repo_files(self, model_id: str) -> List[str]:
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

    async def get_paths_info(self, model_id: str, paths: List[str]):
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
            raise HuggingFaceAPIError(f"Failed to get paths info for {model_id}: {str(e)}") from e

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
        self, limit: int = 10, search: Optional[str] = None, sort: str = "downloads"
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

            # Get model list using client
            models = await self._client.list_models(search=search, sort=sort, limit=limit)

            model_infos = []
            for model in models:
                try:
                    model_info = await self._get_model_details(model.id, model)
                    model_infos.append(model_info)
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

            # Get model information using client
            model = await self._client.get_model_info(model_id)
            result = await self._get_model_details(model_id, model)

            log.info(
                f"Successfully scanned HuggingFace model: model_id={model_id}, file_count={len(result.files)}",
            )
            return result

        except Exception as e:
            log.error(f"Failed to scan HuggingFace model {model_id}: {str(e)}")
            if "not found" in str(e).lower():
                raise HuggingFaceModelNotFoundError(f"Model not found: {model_id}") from e
            raise HuggingFaceAPIError(f"Failed to scan model {model_id}: {str(e)}") from e

    async def _get_model_details(self, model_id: str, model: HfModelInfo) -> ModelInfo:
        """Get detailed model information including file list.

        Args:
            model_id: Model ID
            model: Basic model data from HuggingFace Hub API

        Returns:
            Complete ModelInfo object with all metadata and file list
        """
        # Get file list
        file_infos = await self._get_file_infos(model_id)

        # Extract author
        author = None
        if model.author:
            author = model.author
        elif "/" in model_id:
            author = model_id.split("/")[0]

        # Format dates
        created_at = ""
        last_modified = ""
        if model.created_at:
            created_at = (
                model.created_at.isoformat()
                if isinstance(model.created_at, datetime)
                else str(model.created_at)
            )
        if model.last_modified:
            last_modified = (
                model.last_modified.isoformat()
                if isinstance(model.last_modified, datetime)
                else str(model.last_modified)
            )

        return ModelInfo(
            id=model_id,
            name=model_id.split("/")[-1],
            author=author,
            tags=model.tags or [],
            pipeline_tag=model.pipeline_tag,
            downloads=model.downloads or 0,
            likes=model.likes or 0,
            created_at=created_at,
            last_modified=last_modified,
            files=file_infos,
        )

    async def _get_file_infos(self, model_id: str) -> List[FileInfo]:
        """Get model file information list as FileInfo objects.

        Args:
            model_id: Model ID

        Returns:
            List of FileInfo objects
        """
        try:
            # Get file list using client
            files = await self._client.list_repo_files(model_id)

            # Get detailed info for all files at once for efficiency
            file_info_response = await self._client.get_paths_info(model_id, files)
            file_infos = []

            for info in file_info_response:
                try:
                    if isinstance(info, RepoFile):
                        file_obj = FileInfo(
                            path=info.path,
                            size=info.size,
                            type="file",
                            download_url=self._client.get_download_url(model_id, info.path),
                        )
                    elif isinstance(info, RepoFolder):
                        file_obj = FileInfo(
                            path=info.path,
                            size=0,  # Folders don't have size
                            type="directory",
                            download_url=self._client.get_download_url(model_id, info.path),
                        )
                    else:
                        # Fallback for unknown types
                        file_obj = FileInfo(
                            path=getattr(info, "path", "unknown"),
                            size=0,
                            type="file",
                            download_url=self._client.get_download_url(
                                model_id, getattr(info, "path", "unknown")
                            ),
                        )

                    file_infos.append(file_obj)

                except Exception as e:
                    # If file information cannot be processed
                    path = getattr(info, "path", "unknown")
                    file_obj = FileInfo(
                        path=path,
                        size=0,
                        type="file",
                        download_url=self._client.get_download_url(model_id, path),
                        error=str(e),
                    )
                    file_infos.append(file_obj)

            return file_infos

        except Exception as e:
            log.error(f"Error getting file list for {model_id}: {str(e)}")
            return []

    def get_download_url(self, model_id: str, filename: str) -> str:
        """Generate download URL for a specific file.

        Args:
            model_id: HuggingFace model ID
            filename: File name

        Returns:
            Download URL
        """
        return self._client.get_download_url(model_id, filename)
