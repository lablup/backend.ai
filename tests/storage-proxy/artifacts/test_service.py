"""Tests for HuggingFace Service implementation."""

import uuid
from datetime import datetime
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.storage.registries.types import FileInfo, ModelInfo, ModelTarget
from ai.backend.storage.client.huggingface import HuggingFaceClient
from ai.backend.storage.config.unified import HuggingfaceConfig
from ai.backend.storage.exception import (
    HuggingFaceAPIError,
    RegistryNotFoundError,
)
from ai.backend.storage.services.artifacts.huggingface import (
    HuggingFaceService,
    HuggingFaceServiceArgs,
)
from ai.backend.storage.services.storages import StorageService


@pytest.fixture
def mock_huggingface_config() -> HuggingfaceConfig:
    """Mock HuggingfaceConfig object."""
    return HuggingfaceConfig(
        type="huggingface", token="test_token", endpoint="https://huggingface.co"
    )


@pytest.fixture
def mock_background_task_manager() -> MagicMock:
    """Mock BackgroundTaskManager."""
    mock_manager = MagicMock(spec=BackgroundTaskManager)
    mock_manager.start = AsyncMock(return_value=uuid.uuid4())
    return mock_manager


@pytest.fixture
def mock_storage_service() -> MagicMock:
    """Mock StorageService."""
    mock_service = MagicMock(spec=StorageService)
    mock_service.stream_upload = AsyncMock()
    return mock_service


@pytest.fixture
def mock_registry_configs(
    mock_huggingface_config: HuggingfaceConfig,
) -> dict[str, HuggingfaceConfig]:
    """Mock registry configurations."""
    return {"test_registry": mock_huggingface_config}


@pytest.fixture
def hf_service(
    mock_registry_configs: dict[str, HuggingfaceConfig],
    mock_background_task_manager: MagicMock,
    mock_storage_service: MagicMock,
) -> HuggingFaceService:
    """Create HuggingFaceService instance for testing."""
    args = HuggingFaceServiceArgs(
        registry_configs=mock_registry_configs,
        background_task_manager=mock_background_task_manager,
        storage_service=mock_storage_service,
    )
    return HuggingFaceService(args)


@pytest.fixture
def mock_model_info() -> ModelInfo:
    """Mock ModelInfo object."""
    return ModelInfo(
        id="microsoft/DialoGPT-medium",
        name="DialoGPT-medium",
        author="microsoft",
        tags=["pytorch", "text-generation"],
        created_at=datetime(2021, 1, 1),
        modified_at=datetime(2023, 6, 15),
    )


@pytest.fixture
def mock_file_info() -> FileInfo:
    """Mock FileInfo object."""
    return FileInfo(
        path="config.json",
        size=285,
        type="file",
        download_url="https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json",
    )


@pytest.fixture
def mock_progress_reporter() -> MagicMock:
    """Mock ProgressReporter."""
    mock_reporter = MagicMock(spec=ProgressReporter)
    mock_reporter.update = AsyncMock()
    mock_reporter.total_progress = 0
    return mock_reporter


class TestHuggingFaceService:
    """Test cases for HuggingFaceService."""

    def test_make_scanner_registry_not_found(self, hf_service: HuggingFaceService) -> None:
        """Test scanner creation with registry not found."""
        with pytest.raises(RegistryNotFoundError):
            hf_service._make_scanner("nonexistent_registry")

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_success(
        self,
        mock_list_models: MagicMock,
        hf_service: HuggingFaceService,
        mock_model_info: ModelInfo,
    ) -> None:
        """Test successful models scanning."""
        # Mock the HuggingFace API response
        mock_hf_model = MagicMock()
        mock_hf_model.id = "microsoft/DialoGPT-medium"
        mock_hf_model.author = "microsoft"
        mock_hf_model.tags = ["pytorch", "text-generation"]
        mock_hf_model.created_at = datetime(2021, 1, 1)
        mock_hf_model.last_modified = datetime(2023, 6, 15)
        mock_list_models.return_value = [mock_hf_model]

        models = await hf_service.scan_models(
            registry_name="test_registry", limit=5, search="DialoGPT", sort="downloads"
        )

        assert len(models) == 1
        assert models[0].id == "microsoft/DialoGPT-medium"
        assert models[0].name == "DialoGPT-medium"
        assert models[0].author == "microsoft"
        assert models[0].tags == ["pytorch", "text-generation"]

        mock_list_models.assert_called_once_with(
            search="DialoGPT", sort="downloads", direction=-1, limit=5, token="test_token"
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_api_error(
        self, mock_list_models: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test models scanning with API error."""
        mock_list_models.side_effect = Exception("API Error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_service.scan_models(registry_name="test_registry", limit=10)

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_success(
        self, mock_model_info: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test successful single model scanning."""
        # Mock the HuggingFace API response
        mock_hf_model = MagicMock()
        mock_hf_model.id = "microsoft/DialoGPT-medium"
        mock_hf_model.author = "microsoft"
        mock_hf_model.tags = ["pytorch", "text-generation"]
        mock_hf_model.created_at = datetime(2021, 1, 1)
        mock_hf_model.last_modified = datetime(2023, 6, 15)
        mock_model_info.return_value = mock_hf_model

        model_target = ModelTarget(model_id="microsoft/DialoGPT-medium")
        model = await hf_service.scan_model(registry_name="test_registry", model=model_target)

        assert model.id == "microsoft/DialoGPT-medium"
        assert model.name == "DialoGPT-medium"
        assert model.author == "microsoft"
        assert model.tags == ["pytorch", "text-generation"]

        mock_model_info.assert_called_once_with(
            "microsoft/DialoGPT-medium", revision="main", token="test_token"
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_not_found(
        self, mock_model_info: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test single model scanning with model not found."""
        mock_model_info.side_effect = Exception("not found")

        with pytest.raises(HuggingFaceAPIError):
            model_target = ModelTarget(model_id="nonexistent/model")
            await hf_service.scan_model(registry_name="test_registry", model=model_target)

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_api_error(
        self, mock_model_info: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test single model scanning with API error."""
        mock_model_info.side_effect = Exception("Network error")

        with pytest.raises(HuggingFaceAPIError):
            model_target = ModelTarget(model_id="microsoft/DialoGPT-medium")
            await hf_service.scan_model(registry_name="test_registry", model=model_target)

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_repo_files")
    async def test_list_model_files_success(
        self,
        mock_list_repo_files: MagicMock,
        hf_service: HuggingFaceService,
        mock_file_info: FileInfo,
    ) -> None:
        """Test successful model files listing."""
        mock_list_repo_files.return_value = ["config.json"]

        # Mock the RepoFile object properly
        from huggingface_hub.hf_api import RepoFile

        mock_repo_file = MagicMock(spec=RepoFile)
        mock_repo_file.path = "config.json"
        mock_repo_file.size = 285

        # Mock the HfApi get_paths_info method
        with patch.object(HuggingFaceClient, "list_model_files_info") as mock_list_files_info:
            mock_list_files_info.return_value = [mock_repo_file]

            with patch("ai.backend.storage.client.huggingface.hf_hub_url") as mock_hf_hub_url:
                mock_hf_hub_url.return_value = (
                    "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
                )

                model_target = ModelTarget(model_id="microsoft/DialoGPT-medium")
                files = await hf_service.list_model_files(
                    registry_name="test_registry", model=model_target
                )

                assert len(files) == 1
                assert files[0].path == "config.json"
                assert files[0].size == 285
                assert files[0].type == "file"

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_repo_files")
    async def test_list_model_files_api_error(
        self, mock_list_repo_files: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test model files listing with API error."""
        mock_list_repo_files.side_effect = Exception("API Error")

        model_target = ModelTarget(model_id="microsoft/DialoGPT-medium")

        with pytest.raises(HuggingFaceAPIError):
            await hf_service.list_model_files(registry_name="test_registry", model=model_target)

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.hf_hub_url")
    async def test_get_download_url_success(
        self, mock_hf_hub_url: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test download URL generation."""
        mock_hf_hub_url.return_value = (
            "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
        )

        model_target = ModelTarget(model_id="microsoft/DialoGPT-medium")
        url = await hf_service.get_download_url(
            registry_name="test_registry",
            model=model_target,
            filename="config.json",
        )

        assert url == "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
        mock_hf_hub_url.assert_called_once_with(
            repo_id="microsoft/DialoGPT-medium", filename="config.json", revision="main"
        )

    @pytest.mark.asyncio
    async def test_import_model_success(
        self, hf_service: HuggingFaceService, mock_background_task_manager: MagicMock
    ) -> None:
        """Test successful model import."""
        expected_task_id = uuid.uuid4()
        mock_background_task_manager.start.return_value = expected_task_id

        model_target = ModelTarget(model_id="microsoft/DialoGPT-medium")
        task_id = await hf_service.import_model(
            registry_name="test_registry",
            model=model_target,
            storage_name="test_storage",
            bucket_name="test_bucket",
        )

        assert task_id == expected_task_id
        mock_background_task_manager.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_models_batch_success(
        self, hf_service: HuggingFaceService, mock_background_task_manager: MagicMock
    ) -> None:
        """Test successful batch model import."""
        expected_task_id = uuid.uuid4()
        mock_background_task_manager.start.return_value = expected_task_id

        models = [
            ModelTarget(model_id="microsoft/DialoGPT-medium"),
            ModelTarget(model_id="microsoft/DialoGPT-small"),
        ]
        task_id = await hf_service.import_models_batch(
            registry_name="test_registry",
            models=models,
            storage_name="test_storage",
            bucket_name="test_bucket",
        )

        assert task_id == expected_task_id
        mock_background_task_manager.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_make_download_file_stream_success(
        self, mock_client_session: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test successful file download stream."""

        # Create an async generator for iter_chunked
        async def mock_iter_chunked(chunk_size):
            yield b"chunk1"
            yield b"chunk2"

        # Mock aiohttp response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.content.iter_chunked = mock_iter_chunked

        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = []
        async for chunk in hf_service._make_download_file_stream("http://test.com/file"):
            chunks.append(chunk)

        assert chunks == [b"chunk1", b"chunk2"]

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_make_download_file_stream_http_error(
        self, mock_client_session: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test file download stream with HTTP error."""
        # Mock aiohttp response with error status
        mock_response = MagicMock()
        mock_response.status = 404

        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(HuggingFaceAPIError):
            async for chunk in hf_service._make_download_file_stream("http://test.com/file"):
                pass

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_make_download_file_stream_client_error(
        self, mock_client_session: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test file download stream with client error."""
        mock_client_session.side_effect = ClientError("Connection error")

        with pytest.raises(HuggingFaceAPIError):
            async for chunk in hf_service._make_download_file_stream("http://test.com/file"):
                pass

    @pytest.mark.asyncio
    async def test_upload_model_file_success(
        self,
        hf_service: HuggingFaceService,
        mock_file_info: FileInfo,
        mock_storage_service: MagicMock,
    ) -> None:
        """Test successful model file upload."""
        # Mock successful upload result
        mock_upload_result = MagicMock()
        mock_upload_result.success = True
        mock_storage_service.stream_upload.return_value = mock_upload_result

        # Mock the download stream
        with patch.object(hf_service, "_make_download_file_stream") as mock_download_stream:
            mock_download_stream.return_value = AsyncIterator[bytes]

            await hf_service._upload_single_file_to_storage(
                file_info=mock_file_info,
                model_id="microsoft/DialoGPT-medium",
                revision="main",
                storage_name="test_storage",
                bucket_name="test_bucket",
            )

            mock_storage_service.stream_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_model_file_upload_failure(
        self,
        hf_service: HuggingFaceService,
        mock_file_info: FileInfo,
        mock_storage_service: MagicMock,
    ) -> None:
        """Test model file upload with upload failure."""
        # Mock failed upload result
        mock_upload_result = MagicMock()
        mock_upload_result.success = False
        mock_storage_service.stream_upload.return_value = mock_upload_result

        # Mock the download stream
        with patch.object(hf_service, "_make_download_file_stream") as mock_download_stream:
            mock_download_stream.return_value = AsyncIterator[bytes]

            await hf_service._upload_single_file_to_storage(
                file_info=mock_file_info,
                model_id="microsoft/DialoGPT-medium",
                revision="main",
                storage_name="test_storage",
                bucket_name="test_bucket",
            )

    @pytest.mark.asyncio
    async def test_upload_model_file_no_storage_service(
        self,
        mock_registry_configs: dict[str, HuggingfaceConfig],
        mock_background_task_manager: MagicMock,
        mock_file_info: FileInfo,
    ) -> None:
        """Test model file upload with no storage service configured."""
        # Create service without storage service
        with patch.object(HuggingFaceService, "__init__", lambda self, args: None):
            service = HuggingFaceService.__new__(HuggingFaceService)
            service._registry_configs = mock_registry_configs
            service._background_task_manager = mock_background_task_manager
            service._storages_service = None  # type: ignore

        with pytest.raises(HuggingFaceAPIError):
            await service._upload_single_file_to_storage(
                file_info=mock_file_info,
                model_id="microsoft/DialoGPT-medium",
                revision="main",
                storage_name="test_storage",
                bucket_name="test_bucket",
            )

    @pytest.mark.asyncio
    async def test_upload_model_file_exception(
        self,
        hf_service: HuggingFaceService,
        mock_file_info: FileInfo,
        mock_storage_service: MagicMock,
    ) -> None:
        """Test model file upload with exception."""
        mock_storage_service.stream_upload.side_effect = Exception("Upload error")

        # Mock the download stream
        with patch.object(hf_service, "_make_download_file_stream") as mock_download_stream:
            mock_download_stream.return_value = AsyncIterator[bytes]

        with pytest.raises(HuggingFaceAPIError):
            await hf_service._upload_single_file_to_storage(
                file_info=mock_file_info,
                model_id="microsoft/DialoGPT-medium",
                revision="main",
                storage_name="test_storage",
                bucket_name="test_bucket",
            )
