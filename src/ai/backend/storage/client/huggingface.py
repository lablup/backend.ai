"""HuggingFace client implementation for Backend.AI storage."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import aiohttp
from huggingface_hub import (
    HfApi,
    hf_hub_url,
    list_models,
    list_repo_files,
    list_repo_refs,
    model_info,
)
from huggingface_hub.hf_api import ModelInfo as HfModelInfo
from huggingface_hub.hf_api import RepoFile, RepoFolder

from ai.backend.common.data.storage.registries.types import (
    FileObjectData,
    ModelData,
    ModelSortKey,
    ModelTarget,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import HuggingFaceAPIError

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
        self, limit: int, sort: ModelSortKey, search: Optional[str] = None
    ) -> list[HfModelInfo]:
        """List models from HuggingFace Hub.

        Args:
            limit: Maximum number of models to retrieve
            sort: Sort criteria
            search: Search query to filter models

        Returns:
            List of HfModelInfo objects
        """
        try:
            models = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list_models(
                    search=search,
                    sort=sort.value,
                    direction=-1,  # Descending order
                    limit=limit,
                    token=self._token,
                ),
            )
            return list(models)
        except Exception as e:
            log.error(f"Failed to list models: {str(e)}")
            raise HuggingFaceAPIError(f"Failed to list models: {str(e)}") from e

    async def list_model_revisions(self, model_id: str) -> list[str]:
        """List all available revisions (branches and tags) for a model.

        Args:
            model_id: HuggingFace model ID

        Returns:
            List of revision names
        """
        try:
            refs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list_repo_refs(model_id, token=self._token)
            )
            revisions = []
            for branch in refs.branches:
                revisions.append(branch.name)

            # TODO: Should we consider tag?
            # for tag in refs.tags:
            #     revisions.append(tag.name)
            return revisions
        except Exception as e:
            log.error(f"Failed to list revisions for {model_id}: {str(e)}")
            # Fall back to main revision if revision listing fails
            return ["main"]

    async def scan_model(self, model: ModelTarget) -> HfModelInfo:
        """Get detailed information about a specific model.

        Args:
            model: HuggingFace model to scan

        Returns:
            HfModelInfo object with model metadata
        """
        model_id = model.model_id
        revision = model.revision
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: model_info(model_id, revision=revision, token=self._token)
            )
            return result
        except Exception as e:
            log.error(f"Failed to get model info for {model_id}@{revision}: {str(e)}")
            raise HuggingFaceAPIError(
                f"Failed to get model info for {model_id}@{revision}: {str(e)}"
            ) from e

    async def list_model_filepaths(self, model: ModelTarget) -> list[str]:
        """List files in a model repository.

        Args:
            model: HuggingFace model

        Returns:
            List of file paths
        """
        model_id = model.model_id
        revision = model.revision
        try:
            filepaths = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list_repo_files(model_id, revision=revision, token=self._token)
            )
            return filepaths
        except Exception as e:
            log.error(f"Failed to list files for {model_id}@{revision}: {str(e)}")
            raise HuggingFaceAPIError(
                f"Failed to list files for {model_id}@{revision}: {str(e)}"
            ) from e

    async def list_model_files_info(
        self, model: ModelTarget, paths: list[str]
    ) -> list[RepoFile | RepoFolder]:
        """Get information about specific paths in a repository.

        Args:
            model: HuggingFace model to scan
            paths: List of file paths to get info for

        Returns:
            List of RepoFile or RepoFolder objects
        """
        model_id = model.model_id
        revision = model.revision

        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._api.get_paths_info(
                    model_id, paths=paths, revision=revision, repo_type="model"
                ),
            )
            return info
        except Exception as e:
            log.error(f"Failed to get paths info for {model_id}@{revision} ({paths}): {str(e)}")
            raise HuggingFaceAPIError(
                f'Failed to get paths info for "{model_id}@{revision}": {str(e)}'
            ) from e

    def get_download_url(self, model: ModelTarget, filename: str) -> str:
        """Generate download URL for a specific file.

        Args:
            model: HuggingFace model
            filename: File name

        Returns:
            Download URL
        """
        try:
            return hf_hub_url(repo_id=model.model_id, filename=filename, revision=model.revision)
        except Exception:
            # Fallback URL
            return f"https://huggingface.co/{model.model_id}/resolve/{model.revision}/{filename}"


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
        limit: int,
        sort: ModelSortKey,
        search: Optional[str] = None,
    ) -> list[ModelData]:
        """Scan HuggingFace models concurrently and retrieve metadata for all revisions."""
        try:
            log.info(f"Scanning HuggingFace models: limit={limit}, search={search}, sort={sort}")
            models = await self._client.scan_models(search=search, sort=sort, limit=limit)
            if not models:
                log.info("No models returned from scan_models()")
                return []

            async def build_model_data_for_revisions(model: HfModelInfo) -> list[ModelData]:
                """Build ModelData objects for all revisions of a single model."""
                model_data_list = []
                try:
                    # Get all revisions for this model
                    revisions = await self._client.list_model_revisions(model.id)

                    for revision in revisions:
                        filename = model.id.split("/")[-1]
                        model_data = ModelData(
                            id=model.id,
                            name=filename,
                            author=model.author,
                            revision=revision,
                            tags=model.tags or [],
                            created_at=model.created_at,
                            modified_at=model.last_modified,
                            readme=None,
                        )
                        model_data_list.append(model_data)

                except Exception as e:
                    # Log and skip this entire model if we can't get revisions
                    log.warning(
                        f"Failed to get revisions for model: model_id={model.id}, error={str(e)}"
                    )

                return model_data_list

            # Fire tasks concurrently and collect results
            tasks = [asyncio.create_task(build_model_data_for_revisions(m)) for m in models]
            results = await asyncio.gather(*tasks, return_exceptions=False)

            # Flatten the list of lists
            model_infos: list[ModelData] = []
            for model_data_list in results:
                model_infos.extend(model_data_list)

            log.info(f"Successfully scanned HuggingFace models: count={len(model_infos)}")
            return model_infos

        except Exception as e:
            log.error(f"Failed to scan HuggingFace models: {str(e)}")
            raise HuggingFaceAPIError(f"Failed to scan models: {str(e)}") from e

    async def scan_model(self, model: ModelTarget) -> ModelData:
        """Scan a specific model by ID.

        Args:
            model: HuggingFace model to scan

        Returns:
            ModelData object with model metadata and files
        """
        model_id = model.model_id
        revision = model.revision

        try:
            log.info(f"Scanning specific HuggingFace model: model_id={model_id}@{revision}")
            model_info = await self._client.scan_model(model)

            readme_content = await self._download_readme(model)

            result = ModelData(
                id=model_id,
                name=model_id.split("/")[-1],
                author=model_info.author,
                revision=revision,
                tags=model_info.tags or [],
                created_at=model_info.created_at,
                modified_at=model_info.last_modified,
                readme=readme_content,
            )

            log.info(
                f"Successfully scanned HuggingFace model: model_id={model_id}@{revision}",
            )
            return result

        except Exception as e:
            log.error(f"Failed to scan HuggingFace model {model_id}@{revision}: {str(e)}")
            raise HuggingFaceAPIError(
                f"Failed to scan model {model_id}@{revision}: {str(e)}"
            ) from e

    def get_download_url(self, model: ModelTarget, filename: str) -> str:
        """Generate download URL for a specific file.

        Args:
            model: HuggingFace model
            filename: File name

        Returns:
            Download URL
        """
        return self._client.get_download_url(model, filename)

    async def list_model_files_info(self, model: ModelTarget) -> list[FileObjectData]:
        """Get model file information list as FileInfo objects.

        Args:
            model: HuggingFace model

        Returns:
            List of FileInfo objects
        """
        model_id = model.model_id
        revision = model.revision

        try:
            filepaths = await self._client.list_model_filepaths(model)
            model_files = await self._client.list_model_files_info(model, filepaths)
            file_infos = []

            for file in model_files:
                try:
                    match file:
                        case RepoFile():
                            file_obj = FileObjectData(
                                path=file.path,
                                size=file.size,
                                type="file",
                                download_url=self._client.get_download_url(model, file.path),
                            )
                        case RepoFolder():
                            file_obj = FileObjectData(
                                path=file.path,
                                size=0,
                                type="directory",
                                download_url=self._client.get_download_url(model, file.path),
                            )
                        case _:
                            log.error("Unknown file type for {}, skipping...", file)
                            continue
                    file_infos.append(file_obj)

                except Exception as e:
                    path = getattr(file, "path", "unknown")
                    log.error(
                        f"Error processing file {path} info for model {model_id}@{revision}. Details: {str(e)}"
                    )
                    continue

            return file_infos

        except Exception as e:
            log.error(f"Failed to list files for model {model_id}@{revision}: {str(e)}")
            raise HuggingFaceAPIError(
                f"Failed to list files for model {model_id}@{revision}: {str(e)}"
            ) from e

    async def _download_readme(self, model: ModelTarget) -> Optional[str]:
        """Download README content for a model.

        Args:
            model: HuggingFace model to download README for

        Returns:
            README content as string, or None if download fails
        """
        try:
            readme_url = self._client.get_download_url(model, "README.md")

            async with aiohttp.ClientSession() as session:
                async with session.get(readme_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return content
                    else:
                        log.warning(
                            f"Failed to download README for {model.model_id}@{model.revision}: HTTP {response.status}"
                        )
                        return None

        except Exception as e:
            log.warning(
                f"Failed to download README for {model.model_id}@{model.revision}: {str(e)}"
            )
            return None
