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
from huggingface_hub.errors import (
    GatedRepoError,
)
from huggingface_hub.hf_api import ModelInfo as HfModelInfo
from huggingface_hub.hf_api import RepoFile, RepoFolder

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import (
    FileObjectData,
    ModelData,
    ModelSortKey,
    ModelTarget,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import (
    ModelMetadataFetchDoneEvent,
    ModelMetadataInfo,
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
            revisions = set()
            for branch in refs.branches:
                revisions.add(branch.name)
            for tag in refs.tags:
                revisions.add(tag.name)
            return list(revisions)
        except GatedRepoError:
            # Just return the main branch for gated repos
            return ["main"]
        except Exception as e:
            # TODO: Improve exception handling
            log.warning(
                f"Failed to list revisions for {model_id}: {str(e)}, skipping and fallback to main..."
            )
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
        revision = model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: model_info(model_id, revision=revision, token=self._token)
            )
            return result
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to get model info for {model}: {str(e)}") from e

    async def list_model_filepaths(self, model: ModelTarget) -> list[str]:
        """List files in a model repository.

        Args:
            model: HuggingFace model

        Returns:
            List of file paths
        """
        model_id = model.model_id
        revision = model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        try:
            filepaths = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list_repo_files(model_id, revision=revision, token=self._token)
            )
            return filepaths
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to list files for {model}: {str(e)}") from e

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
        revision = model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)

        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._api.get_paths_info(
                    model_id, paths=paths, revision=revision, repo_type="model"
                ),
            )
            return info
        except Exception as e:
            raise HuggingFaceAPIError(f'Failed to get paths info for "{model}": {str(e)}') from e

    def get_download_url(self, model: ModelTarget, filename: str) -> str:
        """Generate download URL for a specific file.

        Args:
            model: HuggingFace model
            filename: File name

        Returns:
            Download URL
        """
        return hf_hub_url(
            repo_id=model.model_id,
            filename=filename,
            revision=model.resolve_revision(ArtifactRegistryType.HUGGINGFACE),
            endpoint=self._endpoint,
            repo_type="model",
        )


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

            async def build_model_data_per_revision(model: HfModelInfo) -> list[ModelData]:
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
                            size=None,
                        )
                        model_data_list.append(model_data)

                except Exception as e:
                    # Log and skip this entire model if we can't get revisions
                    log.warning(
                        f"Failed to get revisions for model: model_id={model.id}, error={str(e)}"
                    )

                return model_data_list

            # Fire tasks concurrently and collect results
            tasks = [asyncio.create_task(build_model_data_per_revision(m)) for m in models]
            task_results = await asyncio.gather(*tasks, return_exceptions=False)

            # Flatten the list of lists
            result: list[ModelData] = []
            for model_data_list in task_results:
                result.extend(model_data_list)

            log.info(f"Successfully scanned HuggingFace models: count={len(result)}")
            return result

        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to scan models: {str(e)}") from e

    async def scan_model(self, model: ModelTarget) -> ModelData:
        """Scan a specific model by ID.

        Args:
            model: HuggingFace model to scan

        Returns:
            ModelData object with model metadata and files
        """
        try:
            log.info(f"Scanning specific HuggingFace model: {model}")
            model_info = await self._client.scan_model(model)
            total_size = await self._calculate_model_size(model)
            readme_content = await self._download_readme(model)

            model_id = model.model_id
            result = ModelData(
                id=model_id,
                name=model_id.split("/")[-1],
                author=model_info.author,
                revision=model.resolve_revision(ArtifactRegistryType.HUGGINGFACE),
                tags=model_info.tags or [],
                created_at=model_info.created_at,
                modified_at=model_info.last_modified,
                readme=readme_content,
                size=total_size,
            )

            log.info(
                f"Successfully scanned HuggingFace model: {model}",
            )
            return result

        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to scan model {model}: {str(e)}") from e

    async def scan_model_without_metadata(self, model: ModelTarget) -> ModelData:
        """Scan a specific model by ID without README and size metadata.

        Args:
            model: HuggingFace model to scan

        Returns:
            ModelData object with basic metadata only (without README and size)
        """
        try:
            log.info(f"Scanning HuggingFace model without metadata: {model}")
            model_info = await self._client.scan_model(model)

            model_id = model.model_id
            result = ModelData(
                id=model_id,
                name=model_id.split("/")[-1],
                author=model_info.author,
                revision=model.resolve_revision(ArtifactRegistryType.HUGGINGFACE),
                tags=model_info.tags or [],
                created_at=model_info.created_at,
                modified_at=model_info.last_modified,
                readme=None,
                size=None,
            )

            log.info(
                f"Successfully scanned HuggingFace model without metadata: {model}",
            )
            return result

        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to scan model {model}: {str(e)}") from e

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
            List of FileObjectData
        """
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
                        f"Error processing file {path} info for model {model}. Details: {str(e)}"
                    )
                    continue

            return file_infos

        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to list files for model {model}: {str(e)}") from e

    async def download_metadata_batch(
        self,
        models: list[ModelData],
        registry_name: str,
        event_producer: EventProducer,
        max_concurrent: int = 8,
    ) -> None:
        """Download metadata (README and file size) for all models and fire event when complete.

        Args:
            models: List of ModelData objects to download metadata for
            registry_name: Name of the registry (e.g., HuggingFace registry name)
            event_producer: Event producer to fire the completion event
            max_concurrent: Maximum number of concurrent metadata downloads (default: 8)
        """
        log.info(
            f"Starting batch metadata processing for {len(models)} models (max_concurrent={max_concurrent})"
        )
        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_metadata(model_data: ModelData) -> None:
            """Download metadata (README and file size) for a single model."""
            async with semaphore:
                try:
                    model_target = ModelTarget(model_id=model_data.id, revision=model_data.revision)
                    total_size = await self._calculate_model_size(model_target)
                    readme_content = await self._download_readme(model_target)

                    # Only add to results if we have README content
                    if readme_content:
                        metadata_info = ModelMetadataInfo(
                            model_id=model_data.id,
                            revision=model_data.revision,
                            readme_content=readme_content,
                            registry_type=ArtifactRegistryType.HUGGINGFACE,
                            registry_name=registry_name,
                            size=total_size,
                        )
                        await event_producer.anycast_event(
                            ModelMetadataFetchDoneEvent(model=metadata_info)
                        )
                except Exception as e:
                    log.warning(f"Failed to download metadata for {model_data.id}: {str(e)}")

        # Download metadata concurrently with semaphore limit
        tasks = [download_metadata(model) for model in models]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def download_metadata_batch_sync(
        self,
        models: list[ModelData],
        max_concurrent: int = 8,
    ) -> None:
        """Download metadata (README and file size) for all models synchronously and update model objects.

        Args:
            models: List of ModelData objects to download metadata for and update in-place
            max_concurrent: Maximum number of concurrent metadata downloads (default: 8)
        """
        log.info(
            f"Starting synchronous batch metadata processing for {len(models)} models (max_concurrent={max_concurrent})"
        )
        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_and_update_metadata(model_data: ModelData) -> None:
            """Download metadata (README and file size) for a single model and update it in-place."""
            async with semaphore:
                try:
                    model_target = ModelTarget(model_id=model_data.id, revision=model_data.revision)
                    total_size = await self._calculate_model_size(model_target)
                    readme_content = await self._download_readme(model_target)

                    # Update the model data with README content and size
                    model_data.readme = readme_content
                    model_data.size = total_size
                except Exception as e:
                    log.warning(f"Failed to download metadata for {model_data.id}: {str(e)}")

        # Download metadata concurrently with semaphore limit
        tasks = [download_and_update_metadata(model) for model in models]
        await asyncio.gather(*tasks, return_exceptions=True)

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
                            f"Failed to download README for {model}, status code: {response.status}"
                        )
                        return None

        except Exception as e:
            log.warning(f"Failed to download README for {model}: {str(e)}")
            return None

    async def _calculate_model_size(self, model: ModelTarget) -> int:
        try:
            file_infos = await self.list_model_files_info(model)
            return sum(file.size for file in file_infos)
        except Exception as size_error:
            log.warning(f"Failed to calculate size for {model}: {str(size_error)}")
            return 0
