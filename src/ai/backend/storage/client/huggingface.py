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
from ai.backend.storage.errors import HuggingFaceAPIError, HuggingFaceGatedRepoError

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

    def __init__(self, args: HuggingFaceClientArgs) -> None:
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
                    expand=["gated"],
                ),
            )
            return list(models)
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to list models: {e!s}") from e

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
                f"Failed to list revisions for {model_id}: {e!s}, skipping and fallback to main..."
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
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model_info(
                    model_id, revision=revision, token=self._token, expand=["gated"]
                ),
            )
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to get model info for {model}: {e!s}") from e

    async def get_model_commit_hash(self, model: ModelTarget) -> Optional[str]:
        """Get the commit hash for a specific model revision.

        Args:
            model: HuggingFace model with specific revision

        Returns:
            The commit hash (SHA) for the model revision, or None if not available
        """
        model_id = model.model_id
        revision = model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: model_info(model_id, revision=revision, token=self._token)
            )
            return result.sha
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to get commit hash for {model}: {e!s}") from e

    async def list_model_filepaths(self, model: ModelTarget) -> list[str]:
        """List files in a model repository.

        Args:
            model: HuggingFace model

        Returns:
            List of file paths

        Raises:
            GatedRepoError: If the repository is gated and access is denied
            HuggingFaceAPIError: If API call fails
        """
        model_id = model.model_id
        revision = model.resolve_revision(ArtifactRegistryType.HUGGINGFACE)
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: list_repo_files(model_id, revision=revision, token=self._token)
            )
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to list files for {model}: {e!s}") from e

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
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._api.get_paths_info(
                    model_id, paths=paths, revision=revision, repo_type="model"
                ),
            )
        except Exception as e:
            raise HuggingFaceAPIError(f'Failed to get paths info for "{model}": {e!s}') from e

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

    def __init__(self, client: HuggingFaceClient) -> None:
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
                            sha=None,
                            extra={"gated": model.gated},
                        )
                        model_data_list.append(model_data)

                except Exception as e:
                    # Log and skip this entire model if we can't get revisions
                    log.warning(
                        f"Failed to get revisions for model: model_id={model.id}, error={e!s}"
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
            raise HuggingFaceAPIError(f"Failed to scan models: {e!s}") from e

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

            # For gated repos, verify access by checking if we can access a file
            if model_info.gated:
                has_access = await self._check_gated_repo_access(model)
                if not has_access:
                    raise HuggingFaceGatedRepoError(
                        f"Model {model.model_id} is a gated repository and requires authorization to access"
                    )

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
                sha=None,
                extra={"gated": model_info.gated},
            )

            log.info(
                f"Successfully scanned HuggingFace model: {model}",
            )
            return result

        except HuggingFaceGatedRepoError:
            raise
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to scan model {model}: {e!s}") from e

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

            # For gated repos, verify access by checking if we can access a file
            if model_info.gated:
                has_access = await self._check_gated_repo_access(model)
                if not has_access:
                    raise HuggingFaceGatedRepoError(
                        f"Model {model.model_id} is a gated repository and requires authorization to access"
                    )

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
                sha=None,
                extra={"gated": model_info.gated},
            )

            log.info(
                f"Successfully scanned HuggingFace model without metadata: {model}",
            )
            return result
        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to scan model {model}: {e!s}") from e

    def get_download_url(self, model: ModelTarget, filename: str) -> str:
        """Generate download URL for a specific file.

        Args:
            model: HuggingFace model
            filename: File name

        Returns:
            Download URL
        """
        return self._client.get_download_url(model, filename)

    async def get_model_commit_hash(self, model: ModelTarget) -> Optional[str]:
        """Get the commit hash for a specific model revision.

        Args:
            model: HuggingFace model with specific revision

        Returns:
            The commit hash (SHA) for the model revision, or None if not available
        """
        return await self._client.get_model_commit_hash(model)

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
                        f"Error processing file {path} info for model {model}. Details: {e!s}"
                    )
                    continue

            return file_infos

        except Exception as e:
            raise HuggingFaceAPIError(f"Failed to list files for model {model}: {e!s}") from e

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
                except Exception:
                    pass

        # Download metadata concurrently with semaphore limit
        tasks = [download_metadata(model) for model in models]
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
                        return await response.text()
                    return None

        except Exception:
            return None

    async def _check_gated_repo_access(self, model: ModelTarget) -> bool:
        """Check if we have access to a gated repository by making a HEAD request.

        Args:
            model: HuggingFace model to check access for

        Returns:
            True if access is granted, False otherwise
        """
        try:
            # Get file list to find a file to check
            filepaths = await self._client.list_model_filepaths(model)
            if not filepaths:
                return True  # No files to check, assume access is granted

            # Try HEAD request on the first file to check access
            test_file = filepaths[0]
            download_url = self._client.get_download_url(model, test_file)

            headers = {}
            if self._client._token:
                headers["Authorization"] = f"Bearer {self._client._token}"

            async with aiohttp.ClientSession() as session:
                async with session.head(
                    download_url, headers=headers, allow_redirects=True
                ) as resp:
                    # 200 or 302 means access granted, 401/403 means denied
                    return resp.status not in (401, 403)
        except Exception as e:
            log.warning(f"Failed to check gated repo access for {model}: {e!s}")
            return False

    async def _calculate_model_size(self, model: ModelTarget) -> int:
        try:
            file_infos = await self.list_model_files_info(model)
            return sum(file.size for file in file_infos)
        except Exception:
            return 0
