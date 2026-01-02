"""Tests for HuggingFace Client and Scanner implementation."""

from datetime import datetime
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from huggingface_hub.hf_api import ModelInfo as HfModelInfo
from huggingface_hub.hf_api import RepoFile, RepoFolder

from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.storage.client.huggingface import (
    HuggingFaceClient,
    HuggingFaceClientArgs,
    HuggingFaceScanner,
)
from ai.backend.storage.errors import HuggingFaceAPIError


@pytest.fixture
def mock_hf_model_info() -> MagicMock:
    """Mock HuggingFace ModelInfo object."""
    mock_model = MagicMock(spec=HfModelInfo)
    mock_model.id = "microsoft/DialoGPT-medium"
    mock_model.author = "microsoft"
    mock_model.tags = ["pytorch", "text-generation"]
    mock_model.created_at = datetime(2021, 1, 1)
    mock_model.last_modified = datetime(2023, 6, 15)
    mock_model.gated = None
    return mock_model


@pytest.fixture
def mock_repo_file() -> MagicMock:
    """Mock RepoFile object."""
    mock_file = MagicMock(spec=RepoFile)
    mock_file.path = "config.json"
    mock_file.size = 285
    return mock_file


@pytest.fixture
def mock_repo_folder() -> MagicMock:
    """Mock RepoFolder object."""
    mock_folder = MagicMock(spec=RepoFolder)
    mock_folder.path = "tokenizer"
    return mock_folder


@pytest.fixture
def hf_client() -> HuggingFaceClient:
    """Create HuggingFaceClient instance for testing."""
    args = HuggingFaceClientArgs(token="test_token", endpoint="https://huggingface.co")
    return HuggingFaceClient(args)


@pytest.fixture
def hf_scanner(hf_client: HuggingFaceClient) -> HuggingFaceScanner:
    """Create HuggingFaceScanner instance for testing."""
    return HuggingFaceScanner(hf_client)


class TestHuggingFaceClient:
    """Test cases for HuggingFaceClient."""

    def test_init(self) -> None:
        """Test HuggingFaceClient initialization."""
        args = HuggingFaceClientArgs(token="test_token", endpoint="https://huggingface.co")
        client = HuggingFaceClient(args)

        assert client._token == "test_token"
        assert client._endpoint == "https://huggingface.co"
        assert client._api is not None

    def test_init_no_token(self) -> None:
        """Test HuggingFaceClient initialization without token."""
        args = HuggingFaceClientArgs(token=None, endpoint=None)
        client = HuggingFaceClient(args)

        assert client._token is None
        assert client._endpoint is None
        assert client._api is not None

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_success(
        self,
        mock_list_models: MagicMock,
        hf_client: HuggingFaceClient,
        mock_hf_model_info: MagicMock,
    ) -> None:
        """Test successful model scanning."""
        mock_list_models.return_value = [mock_hf_model_info]

        models = await hf_client.scan_models(
            search="DialoGPT", sort=ModelSortKey.DOWNLOADS, limit=5
        )

        assert len(models) == 1
        assert models[0].id == "microsoft/DialoGPT-medium"
        mock_list_models.assert_called_once_with(
            search="DialoGPT",
            sort=ModelSortKey.DOWNLOADS,
            direction=-1,
            limit=5,
            token="test_token",
            expand=["gated"],
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_api_error(
        self, mock_list_models: MagicMock, hf_client: HuggingFaceClient
    ) -> None:
        """Test model scanning with API error."""
        mock_list_models.side_effect = Exception("API Error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_client.scan_models(limit=10, sort=ModelSortKey.DOWNLOADS)

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_success(
        self,
        mock_model_info: MagicMock,
        hf_client: HuggingFaceClient,
        mock_hf_model_info: MagicMock,
    ) -> None:
        """Test successful single model scanning."""
        mock_model_info.return_value = mock_hf_model_info

        model = await hf_client.scan_model(ModelTarget(model_id="microsoft/DialoGPT-medium"))

        assert model.id == "microsoft/DialoGPT-medium"
        assert model.author == "microsoft"
        mock_model_info.assert_called_once_with(
            "microsoft/DialoGPT-medium", revision="main", token="test_token"
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_not_found(
        self, mock_model_info: MagicMock, hf_client: HuggingFaceClient
    ) -> None:
        """Test model scanning with model not found."""
        mock_model_info.side_effect = Exception("Model not found")

        with pytest.raises(HuggingFaceAPIError):
            await hf_client.scan_model(ModelTarget(model_id="nonexistent/model"))

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_api_error(
        self, mock_model_info: MagicMock, hf_client: HuggingFaceClient
    ) -> None:
        """Test model scanning with API error."""
        mock_model_info.side_effect = Exception("Network error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_client.scan_model(ModelTarget(model_id="microsoft/DialoGPT-medium"))

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_repo_files")
    async def test_list_model_filepaths_success(
        self, mock_list_repo_files: MagicMock, hf_client: HuggingFaceClient
    ) -> None:
        """Test successful file path listing."""
        mock_list_repo_files.return_value = ["config.json", "pytorch_model.bin", "tokenizer.json"]

        filepaths = await hf_client.list_model_filepaths(
            ModelTarget(model_id="microsoft/DialoGPT-medium")
        )

        assert len(filepaths) == 3
        assert "config.json" in filepaths
        assert "pytorch_model.bin" in filepaths
        assert "tokenizer.json" in filepaths
        mock_list_repo_files.assert_called_once_with(
            "microsoft/DialoGPT-medium", revision="main", token="test_token"
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_repo_files")
    async def test_list_model_filepaths_error(
        self, mock_list_repo_files: MagicMock, hf_client: HuggingFaceClient
    ) -> None:
        """Test file path listing with error."""
        mock_list_repo_files.side_effect = Exception("API Error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_client.list_model_filepaths(ModelTarget(model_id="microsoft/DialoGPT-medium"))

    @pytest.mark.asyncio
    async def test_list_model_files_info_success(
        self, hf_client: HuggingFaceClient, mock_repo_file: MagicMock, mock_repo_folder: MagicMock
    ) -> None:
        """Test successful file info listing."""
        with patch.object(hf_client._api, "get_paths_info") as mock_get_paths_info:
            mock_get_paths_info.return_value = [mock_repo_file, mock_repo_folder]

            files_info = await hf_client.list_model_files_info(
                ModelTarget(model_id="microsoft/DialoGPT-medium"), ["config.json", "tokenizer"]
            )

            assert len(files_info) == 2
            assert files_info[0].path == "config.json"
            assert files_info[1].path == "tokenizer"
            mock_get_paths_info.assert_called_once_with(
                "microsoft/DialoGPT-medium",
                paths=["config.json", "tokenizer"],
                revision="main",
                repo_type="model",
            )

    @pytest.mark.asyncio
    async def test_list_model_files_info_error(self, hf_client: HuggingFaceClient) -> None:
        """Test file info listing with error."""
        with patch.object(hf_client._api, "get_paths_info") as mock_get_paths_info:
            mock_get_paths_info.side_effect = Exception("API Error")

            with pytest.raises(HuggingFaceAPIError):
                await hf_client.list_model_files_info(
                    ModelTarget(model_id="microsoft/DialoGPT-medium"), ["config.json"]
                )

    def test_get_download_url_success(self, hf_client: HuggingFaceClient) -> None:
        """Test download URL generation."""
        with patch("ai.backend.storage.client.huggingface.hf_hub_url") as mock_hf_hub_url:
            mock_hf_hub_url.return_value = (
                "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
            )

            url = hf_client.get_download_url(
                ModelTarget(model_id="microsoft/DialoGPT-medium"), "config.json"
            )

            assert (
                url == "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
            )
            mock_hf_hub_url.assert_called_once_with(
                repo_id="microsoft/DialoGPT-medium",
                filename="config.json",
                revision="main",
                endpoint="https://huggingface.co",
                repo_type="model",
            )

    def test_get_download_url_fallback(self, hf_client: HuggingFaceClient) -> None:
        """Test download URL generation with error."""
        with patch("ai.backend.storage.client.huggingface.hf_hub_url") as mock_hf_hub_url:
            mock_hf_hub_url.side_effect = Exception("Error")

            with pytest.raises(Exception):
                hf_client.get_download_url(
                    ModelTarget(model_id="microsoft/DialoGPT-medium"), "config.json"
                )


class TestHuggingFaceScanner:
    """Test cases for HuggingFaceScanner."""

    def test_init(self, hf_client: HuggingFaceClient) -> None:
        """Test HuggingFaceScanner initialization."""
        scanner = HuggingFaceScanner(hf_client)
        assert scanner._client == hf_client

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_success(
        self,
        mock_list_models: MagicMock,
        hf_scanner: HuggingFaceScanner,
        mock_hf_model_info: MagicMock,
    ) -> None:
        """Test successful models scanning."""
        mock_list_models.return_value = [mock_hf_model_info]

        model_infos = await hf_scanner.scan_models(
            limit=5, search="DialoGPT", sort=ModelSortKey.DOWNLOADS
        )

        assert len(model_infos) == 1
        assert model_infos[0].id == "microsoft/DialoGPT-medium"
        assert model_infos[0].name == "DialoGPT-medium"
        assert model_infos[0].author == "microsoft"
        assert model_infos[0].tags == ["pytorch", "text-generation"]

        mock_list_models.assert_called_once_with(
            search="DialoGPT",
            sort=ModelSortKey.DOWNLOADS,
            direction=-1,
            limit=5,
            token="test_token",
            expand=["gated"],
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_with_error_model(
        self, mock_list_models: MagicMock, hf_scanner: HuggingFaceScanner
    ) -> None:
        """Test models scanning with some models having errors."""
        # Create mock models where one will cause an error
        mock_good_model = MagicMock(spec=HfModelInfo)
        mock_good_model.id = "microsoft/DialoGPT-medium"
        mock_good_model.author = "microsoft"
        mock_good_model.tags = ["pytorch"]
        mock_good_model.created_at = datetime(2021, 1, 1)
        mock_good_model.last_modified = datetime(2023, 6, 15)
        mock_good_model.gated = False

        mock_bad_model = MagicMock(spec=HfModelInfo)
        mock_bad_model.id = None  # This will cause an error

        mock_list_models.return_value = [mock_good_model, mock_bad_model]

        model_infos = await hf_scanner.scan_models(limit=2, sort=ModelSortKey.DOWNLOADS)

        assert len(model_infos) == 1
        assert model_infos[0].id == "microsoft/DialoGPT-medium"

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_api_error(
        self, mock_list_models: MagicMock, hf_scanner: HuggingFaceScanner
    ) -> None:
        """Test models scanning with API error."""
        mock_list_models.side_effect = Exception("API Error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_scanner.scan_models(limit=10, sort=ModelSortKey.DOWNLOADS)

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_success(
        self,
        mock_model_info: MagicMock,
        hf_scanner: HuggingFaceScanner,
        mock_hf_model_info: MagicMock,
    ) -> None:
        """Test successful single model scanning."""
        mock_model_info.return_value = mock_hf_model_info

        model_info = await hf_scanner.scan_model(ModelTarget(model_id="microsoft/DialoGPT-medium"))

        assert model_info.id == "microsoft/DialoGPT-medium"
        assert model_info.name == "DialoGPT-medium"
        assert model_info.author == "microsoft"
        assert model_info.tags == ["pytorch", "text-generation"]

        mock_model_info.assert_called_once_with(
            "microsoft/DialoGPT-medium", revision="main", token="test_token"
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_not_found(
        self, mock_model_info: MagicMock, hf_scanner: HuggingFaceScanner
    ) -> None:
        """Test single model scanning with model not found."""
        mock_model_info.side_effect = Exception("not found")

        with pytest.raises(HuggingFaceAPIError):
            await hf_scanner.scan_model(ModelTarget(model_id="nonexistent/model"))

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.model_info")
    async def test_scan_model_api_error(
        self, mock_model_info: MagicMock, hf_scanner: HuggingFaceScanner
    ) -> None:
        """Test single model scanning with API error."""
        mock_model_info.side_effect = Exception("Network error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_scanner.scan_model(ModelTarget(model_id="microsoft/DialoGPT-medium"))

    @patch("ai.backend.storage.client.huggingface.hf_hub_url")
    def test_get_download_url(
        self, mock_hf_hub_url: MagicMock, hf_scanner: HuggingFaceScanner
    ) -> None:
        """Test download URL generation delegation."""
        mock_hf_hub_url.return_value = (
            "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
        )

        url = hf_scanner.get_download_url(
            ModelTarget(model_id="microsoft/DialoGPT-medium"), "config.json"
        )

        assert url == "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
        mock_hf_hub_url.assert_called_once_with(
            repo_id="microsoft/DialoGPT-medium",
            filename="config.json",
            revision="main",
            endpoint="https://huggingface.co",
            repo_type="model",
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.hf_hub_url")
    @patch("ai.backend.storage.client.huggingface.list_repo_files")
    async def test_list_model_files_info_success(
        self,
        mock_list_repo_files: MagicMock,
        mock_hf_hub_url: MagicMock,
        hf_scanner: HuggingFaceScanner,
        mock_repo_file: MagicMock,
        mock_repo_folder: MagicMock,
    ) -> None:
        """Test successful model files info listing."""
        # Mock the HuggingFace API calls
        mock_list_repo_files.return_value = ["config.json", "tokenizer"]
        mock_hf_hub_url.side_effect = [
            "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json",
            "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/tokenizer",
        ]

        # Mock the HfApi get_paths_info method
        with patch.object(hf_scanner._client._api, "get_paths_info") as mock_get_paths_info:
            mock_get_paths_info.return_value = [mock_repo_file, mock_repo_folder]

            file_infos = await hf_scanner.list_model_files_info(
                ModelTarget(model_id="microsoft/DialoGPT-medium")
            )

            assert len(file_infos) == 2

            # Check file info
            file_info = file_infos[0]
            assert file_info.path == "config.json"
            assert file_info.size == 285
            assert file_info.type == "file"
            assert (
                file_info.download_url
                == "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
            )

            # Check folder info
            folder_info = file_infos[1]
            assert folder_info.path == "tokenizer"
            assert folder_info.size == 0
            assert folder_info.type == "directory"
            assert (
                folder_info.download_url
                == "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/tokenizer"
            )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.hf_hub_url")
    @patch("ai.backend.storage.client.huggingface.list_repo_files")
    async def test_list_model_files_info_with_error_files(
        self,
        mock_list_repo_files: MagicMock,
        mock_hf_hub_url: MagicMock,
        hf_scanner: HuggingFaceScanner,
    ) -> None:
        """Test model files info listing with some files having errors."""
        mock_good_file = MagicMock(spec=RepoFile)
        mock_good_file.path = "config.json"
        mock_good_file.size = 285

        # Create a mock file that will cause an error when accessing .path
        mock_bad_file = MagicMock(spec=RepoFile)
        mock_bad_file.path = PropertyMock(side_effect=Exception("Path access error"))
        mock_bad_file.size = 100

        mock_list_repo_files.return_value = ["config.json", "bad_file"]
        mock_hf_hub_url.return_value = (
            "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"
        )

        with patch.object(hf_scanner._client._api, "get_paths_info") as mock_get_paths_info:
            mock_get_paths_info.return_value = [mock_good_file, mock_bad_file]

            file_infos = await hf_scanner.list_model_files_info(
                ModelTarget(model_id="microsoft/DialoGPT-medium")
            )

            # Should get the good file, bad file should be skipped due to error
            assert len(file_infos) == 1
            assert file_infos[0].path == "config.json"

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_repo_files")
    async def test_list_model_files_info_api_error(
        self, mock_list_repo_files: MagicMock, hf_scanner: HuggingFaceScanner
    ) -> None:
        """Test model files info listing with API error."""
        mock_list_repo_files.side_effect = Exception("API Error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_scanner.list_model_files_info(
                ModelTarget(model_id="microsoft/DialoGPT-medium")
            )
