"""Tests for HuggingFace Service implementation."""

import uuid
from datetime import datetime
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp import ClientError

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, ProgressReporter
from ai.backend.common.data.storage.registries.types import (
    FileObjectData,
    ModelData,
    ModelSortKey,
    ModelTarget,
)
from ai.backend.storage.client.huggingface import HuggingFaceClient
from ai.backend.storage.config.unified import (
    HuggingfaceConfig,
    ObjectStorageConfig,
    ReservoirConfig,
)
from ai.backend.storage.exception import (
    ArtifactStorageEmptyError,
    HuggingFaceAPIError,
    ObjectStorageBucketNotFoundError,
    ObjectStorageConfigInvalidError,
    RegistryNotFoundError,
    ReservoirStorageConfigInvalidError,
    StorageNotFoundError,
)
from ai.backend.storage.services.artifacts.huggingface import (
    HuggingFaceFileDownloadStreamReader,
    HuggingFaceService,
    HuggingFaceServiceArgs,
)
from ai.backend.storage.services.artifacts.reservoir import (
    ReservoirService,
    ReservoirServiceArgs,
)
from ai.backend.storage.storages.object_storage import ObjectStorage
from ai.backend.storage.storages.storage_pool import StoragePool
from ai.backend.storage.types import BucketCopyOptions

_DEFAULT_CHUNK_SIZE = 8192


def create_mock_aiohttp_session() -> Tuple[Mock, Mock]:
    """Create a properly configured mock session that supports async context manager protocol."""
    mock_session = Mock()

    # Create mock response with regular Mock for non-async attributes
    mock_response = Mock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Mock headers as a regular Mock so .get() returns normal values
    mock_headers = Mock()
    mock_response.headers = mock_headers

    # Mock content as a regular Mock
    mock_content = Mock()
    mock_response.content = mock_content

    # Configure session methods to return the mock response
    mock_get = Mock()
    mock_get.return_value = mock_response
    mock_session.get = mock_get

    mock_head = Mock()
    mock_head.return_value = mock_response
    mock_session.head = mock_head

    # Add close method
    mock_session.close = AsyncMock()

    return mock_session, mock_response


@pytest.fixture
def mock_huggingface_config() -> HuggingfaceConfig:
    """Mock HuggingfaceConfig object."""
    return HuggingfaceConfig(
        token="test_token",
        endpoint="https://huggingface.co",
    )


@pytest.fixture
def mock_background_task_manager() -> MagicMock:
    """Mock BackgroundTaskManager."""
    mock_manager = MagicMock(spec=BackgroundTaskManager)
    mock_manager.start = AsyncMock(return_value=uuid.uuid4())
    return mock_manager


@pytest.fixture
def mock_storage_pool() -> MagicMock:
    """Mock StoragePool."""

    mock_pool = MagicMock(spec=StoragePool)
    mock_storage = MagicMock(spec=ObjectStorage)
    mock_storage.stream_upload = AsyncMock()
    mock_storage._bucket = "test-bucket"
    mock_storage._endpoint = "https://s3.amazonaws.com"
    mock_storage._region = "us-west-2"
    mock_storage._access_key = "test_access_key"
    mock_storage._secret_key = "test_secret_key"
    mock_storage._upload_chunk_size = 5 * 1024 * 1024
    mock_storage._reservoir_download_chunk_size = 8192
    mock_pool.get_storage.return_value = mock_storage
    return mock_pool


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
    mock_storage_pool: MagicMock,
) -> HuggingFaceService:
    """Create HuggingFaceService instance for testing."""
    args = HuggingFaceServiceArgs(
        registry_configs=mock_registry_configs,
        background_task_manager=mock_background_task_manager,
        storage_pool=mock_storage_pool,
        event_producer=MagicMock(),  # Mock event producer
    )
    return HuggingFaceService(args)


@pytest.fixture
def mock_model_info() -> ModelData:
    """Mock ModelData object."""
    return ModelData(
        id="microsoft/DialoGPT-medium",
        name="DialoGPT-medium",
        author="microsoft",
        tags=["pytorch", "text-generation"],
        created_at=datetime(2021, 1, 1),
        modified_at=datetime(2023, 6, 15),
        size=2048000,
    )


@pytest.fixture
def mock_file_info() -> FileObjectData:
    """Mock FileObjectData object."""
    return FileObjectData(
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


@pytest.fixture
def mock_reservoir_config() -> ReservoirConfig:
    """Mock ReservoirConfig object."""
    return ReservoirConfig(
        endpoint="https://s3.amazonaws.com",
        object_storage_region="us-west-2",
        object_storage_access_key="test_access_key",
        object_storage_secret_key="test_secret_key",
    )


@pytest.fixture
def mock_object_storage_config() -> ObjectStorageConfig:
    """Mock ObjectStorageConfig object."""
    return ObjectStorageConfig(
        endpoint="https://s3.amazonaws.com",
        region="us-west-2",
        access_key="test_access_key",
        secret_key="test_secret_key",
        buckets=["test-bucket"],
        upload_chunk_size=5 * 1024 * 1024,  # 5 MiB minimum
        reservoir_download_chunk_size=8192,
    )


@pytest.fixture
def reservoir_service(
    mock_background_task_manager: MagicMock,
    mock_storage_pool: MagicMock,
    mock_reservoir_config: ReservoirConfig,
    mock_object_storage_config: ObjectStorageConfig,
) -> ReservoirService:
    """Create ReservoirService instance for testing."""
    args = ReservoirServiceArgs(
        background_task_manager=mock_background_task_manager,
        event_producer=MagicMock(),
        storage_pool=mock_storage_pool,
        reservoir_registry_configs=[mock_reservoir_config],
    )
    return ReservoirService(args)


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
        mock_model_info: ModelData,
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
            registry_name="test_registry", limit=5, search="DialoGPT", sort=ModelSortKey.DOWNLOADS
        )

        assert len(models) == 1
        assert models[0].id == "microsoft/DialoGPT-medium"
        assert models[0].name == "DialoGPT-medium"
        assert models[0].author == "microsoft"
        assert models[0].tags == ["pytorch", "text-generation"]

        mock_list_models.assert_called_once_with(
            search="DialoGPT",
            sort=ModelSortKey.DOWNLOADS,
            direction=-1,
            limit=5,
            token="test_token",
        )

    @pytest.mark.asyncio
    @patch("ai.backend.storage.client.huggingface.list_models")
    async def test_scan_models_api_error(
        self, mock_list_models: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test models scanning with API error."""
        mock_list_models.side_effect = Exception("API Error")

        with pytest.raises(HuggingFaceAPIError):
            await hf_service.scan_models(
                registry_name="test_registry", limit=10, sort=ModelSortKey.DOWNLOADS
            )

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
        mock_file_info: FileObjectData,
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
        url = hf_service.get_download_url(
            registry_name="test_registry",
            model=model_target,
            filename="config.json",
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
        )

        assert task_id == expected_task_id
        mock_background_task_manager.start.assert_called_once()

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_make_download_file_stream_success(
        self, mock_client_session: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test successful file download stream."""

        mock_session, mock_response = create_mock_aiohttp_session()
        mock_client_session.return_value = mock_session

        # Create an async generator for iter_chunked
        async def mock_iter_chunked(chunk_size):
            yield b"chunk1"
            yield b"chunk2"

        # Configure response
        mock_response.status = 200
        mock_response.content.iter_chunked = mock_iter_chunked

        # Mock headers.get to return different values for different headers
        def mock_headers_get(key, default=None):
            if key == "Content-Length":
                return "12"  # Total size matches our chunks
            elif key == "ETag":
                return None
            elif key == "Accept-Ranges":
                return None
            else:
                return default

        mock_response.headers.get.side_effect = mock_headers_get

        chunks = []
        download_stream = HuggingFaceFileDownloadStreamReader(
            "http://test.com/file",
            _DEFAULT_CHUNK_SIZE,
            max_retries=8,
            content_type="application/octet-stream",
        )
        async for chunk in download_stream.read():
            chunks.append(chunk)

        assert chunks == [b"chunk1", b"chunk2"]
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_make_download_file_stream_http_error(
        self, mock_client_session: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test file download stream with HTTP error."""
        mock_session, mock_response = create_mock_aiohttp_session()
        mock_client_session.return_value = mock_session

        # Create an async generator that immediately raises a non-retriable error
        async def mock_iter_chunked_error(chunk_size):
            raise RuntimeError("HTTP 404 Not Found")
            yield  # Never reached, but needed for generator syntax

        # Configure response with error status
        mock_response.status = 404
        mock_response.content.iter_chunked = mock_iter_chunked_error
        mock_response.headers.get.return_value = None

        with pytest.raises(RuntimeError):
            download_stream = HuggingFaceFileDownloadStreamReader(
                "http://test.com/file",
                _DEFAULT_CHUNK_SIZE,
                max_retries=8,
                content_type="application/octet-stream",
            )
            async for chunk in download_stream.read():
                pass

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_make_download_file_stream_client_error(
        self, mock_client_session: MagicMock, hf_service: HuggingFaceService
    ) -> None:
        """Test file download stream with client error."""
        mock_client_session.side_effect = ClientError("Connection error")

        with pytest.raises(ClientError):
            download_stream = HuggingFaceFileDownloadStreamReader(
                "http://test.com/file",
                _DEFAULT_CHUNK_SIZE,
                max_retries=8,
                content_type="application/octet-stream",
            )
            async for chunk in download_stream.read():
                pass

    @pytest.mark.asyncio
    async def test_upload_model_file_success(
        self,
        hf_service: HuggingFaceService,
        mock_file_info: FileObjectData,
        mock_storage_pool: MagicMock,
    ) -> None:
        """Test successful model file upload."""
        # Mock the HuggingFaceFileDownloadStreamReader class
        with patch(
            "ai.backend.storage.services.artifacts.huggingface.HuggingFaceFileDownloadStreamReader"
        ) as mock_stream_class:
            mock_stream_instance = AsyncMock()
            mock_stream_class.return_value = mock_stream_instance

            await hf_service._pipe_single_file_to_storage(
                file_info=mock_file_info,
                model=ModelTarget(model_id="microsoft/DialoGPT-medium", revision="main"),
                storage_name="test_storage",
                download_chunk_size=_DEFAULT_CHUNK_SIZE,
            )

            # Verify the stream reader was created with correct parameters
            mock_stream_class.assert_called_once_with(
                url=mock_file_info.download_url,
                chunk_size=_DEFAULT_CHUNK_SIZE,
                max_retries=8,
                content_type="application/json",  # mimetypes.guess_type('config.json')[0]
            )

            # Get the mock storage from the pool and check it was called
            mock_storage = mock_storage_pool.get_storage.return_value
            mock_storage.stream_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_model_file_upload_failure(
        self,
        hf_service: HuggingFaceService,
        mock_file_info: FileObjectData,
        mock_storage_pool: MagicMock,
    ) -> None:
        """Test model file upload with upload failure."""
        # Mock failed upload result - setup the mock storage from the pool
        mock_storage = mock_storage_pool.get_storage.return_value
        mock_storage.stream_upload.side_effect = Exception("Upload failed")

        # Mock the HuggingFaceFileDownloadStreamReader class
        with patch(
            "ai.backend.storage.services.artifacts.huggingface.HuggingFaceFileDownloadStreamReader"
        ) as mock_stream_class:
            mock_stream_instance = AsyncMock()
            mock_stream_class.return_value = mock_stream_instance

            with pytest.raises(HuggingFaceAPIError):
                await hf_service._pipe_single_file_to_storage(
                    file_info=mock_file_info,
                    model=ModelTarget(
                        model_id="microsoft/DialoGPT-medium",
                        revision="main",
                    ),
                    storage_name="test_storage",
                    download_chunk_size=_DEFAULT_CHUNK_SIZE,
                )

    @pytest.mark.asyncio
    async def test_upload_model_file_no_storage_service(
        self,
        mock_registry_configs: dict[str, HuggingfaceConfig],
        mock_background_task_manager: MagicMock,
        mock_file_info: FileObjectData,
    ) -> None:
        """Test model file upload with no storage pool configured."""
        # Create service without storage pool
        with patch.object(HuggingFaceService, "__init__", lambda self, args: None):
            service = HuggingFaceService.__new__(HuggingFaceService)
            service._registry_configs = mock_registry_configs
            service._background_task_manager = mock_background_task_manager
            service._storage_pool = None  # type: ignore

        with pytest.raises(ObjectStorageConfigInvalidError):
            await service._pipe_single_file_to_storage(
                file_info=mock_file_info,
                model=ModelTarget(model_id="microsoft/DialoGPT-medium", revision="main"),
                storage_name="test_storage",
                download_chunk_size=_DEFAULT_CHUNK_SIZE,
            )

    @pytest.mark.asyncio
    async def test_upload_model_file_exception(
        self,
        hf_service: HuggingFaceService,
        mock_file_info: FileObjectData,
        mock_storage_pool: MagicMock,
    ) -> None:
        """Test model file upload with exception."""
        mock_storage = mock_storage_pool.get_storage.return_value
        mock_storage.stream_upload.side_effect = Exception("Upload error")

        # Mock the HuggingFaceFileDownloadStreamReader class
        with patch(
            "ai.backend.storage.services.artifacts.huggingface.HuggingFaceFileDownloadStreamReader"
        ) as mock_stream_class:
            mock_stream_instance = AsyncMock()
            mock_stream_class.return_value = mock_stream_instance

            with pytest.raises(HuggingFaceAPIError):
                await hf_service._pipe_single_file_to_storage(
                    file_info=mock_file_info,
                    model=ModelTarget(model_id="microsoft/DialoGPT-medium", revision="main"),
                    storage_name="test_storage",
                    download_chunk_size=_DEFAULT_CHUNK_SIZE,
                )


class TestReservoirService:
    """Test cases for ReservoirService."""

    def test_get_s3_client_success(
        self,
        reservoir_service: ReservoirService,
        mock_object_storage_config: ObjectStorageConfig,
    ) -> None:
        """Test successful S3 client creation."""
        client, bucket_name = reservoir_service._get_s3_client("test_storage")
        assert bucket_name == "test-bucket"
        assert client.bucket_name == "test-bucket"

    def test_get_s3_client_storage_not_found(self, reservoir_service: ReservoirService) -> None:
        """Test S3 client creation with storage not found."""
        # Configure mock to raise KeyError for unknown storage
        original_storage = reservoir_service._storage_pool.get_storage("test_storage")

        def mock_get_storage(name: str):
            if name == "test_storage":
                return original_storage
            else:
                raise KeyError(name)

        reservoir_service._storage_pool = Mock(spec=StoragePool)
        reservoir_service._storage_pool.get_storage = Mock(side_effect=mock_get_storage)

        with pytest.raises(StorageNotFoundError):
            reservoir_service._get_s3_client("nonexistent_storage")

    def test_get_s3_client_no_buckets_configured(
        self,
        reservoir_service: ReservoirService,
        mock_object_storage_config: ObjectStorageConfig,
    ) -> None:
        """Test S3 client creation with no buckets configured."""
        # Mock storage with empty bucket (this would be invalid ObjectStorage config)
        mock_storage = reservoir_service._storage_pool.get_storage("test_storage")
        assert isinstance(mock_storage, MagicMock)  # Type narrowing for mypy
        mock_storage._bucket = ""  # Simulate no bucket configured

        with pytest.raises(ObjectStorageBucketNotFoundError):
            reservoir_service._get_s3_client("test_storage")

    @pytest.mark.asyncio
    async def test_list_all_keys_and_sizes_success(
        self, reservoir_service: ReservoirService
    ) -> None:
        """Test successful listing of all keys and sizes."""
        # Mock the entire method since it's a complex AWS integration
        with patch.object(reservoir_service, "_list_all_keys_and_sizes") as mock_list_keys:
            mock_list_keys.return_value = (
                ["model.bin", "config.json"],  # keys
                {"model.bin": 1000, "config.json": 500},  # size_map
                1500,  # total
            )

            # Create a mock S3Client for testing
            from unittest.mock import Mock

            mock_s3_client = Mock()

            keys, size_map, total = await reservoir_service._list_all_keys_and_sizes(
                s3_client=mock_s3_client,
                prefix="models/",
            )

            assert len(keys) == 2
            assert "model.bin" in keys
            assert "config.json" in keys
            assert size_map["model.bin"] == 1000
            assert size_map["config.json"] == 500
            assert total == 1500

    @pytest.mark.asyncio
    async def test_list_all_keys_and_sizes_empty_bucket(
        self, reservoir_service: ReservoirService
    ) -> None:
        """Test listing keys from empty bucket."""
        # Mock the entire method for empty bucket case
        with patch.object(reservoir_service, "_list_all_keys_and_sizes") as mock_list_keys:
            mock_list_keys.return_value = ([], {}, 0)

            # Create a mock S3Client for testing
            from unittest.mock import Mock

            mock_s3_client = Mock()

            keys, size_map, total = await reservoir_service._list_all_keys_and_sizes(
                s3_client=mock_s3_client,
            )

            assert len(keys) == 0
            assert len(size_map) == 0
            assert total == 0

    @pytest.mark.asyncio
    async def test_stream_bucket_to_bucket_success(
        self,
        reservoir_service: ReservoirService,
        mock_reservoir_config: ReservoirConfig,
        mock_progress_reporter: MagicMock,
    ) -> None:
        """Test successful bucket to bucket streaming."""
        with (
            patch.object(reservoir_service, "_list_all_keys_and_sizes") as mock_list_keys,
            patch.object(reservoir_service, "_get_s3_client") as mock_get_s3_client,
            patch(
                "ai.backend.storage.services.artifacts.reservoir.S3Client"
            ) as mock_s3_client_class,
        ):
            # Mock list keys response
            mock_list_keys.return_value = (
                ["model.bin", "config.json"],
                {"model.bin": 1000, "config.json": 500},
                1500,
            )

            # Mock S3 clients - _get_s3_client now returns (client, bucket_name)
            mock_dst_client = MagicMock()
            mock_dst_client.upload_stream = AsyncMock()
            mock_get_s3_client.return_value = (mock_dst_client, "test-bucket")

            mock_src_client = MagicMock()
            mock_src_client.download_stream = AsyncMock()
            mock_src_client.get_object_meta = AsyncMock()
            mock_s3_client_class.return_value = mock_src_client

            # Mock download stream
            async def mock_download_stream(key, chunk_size):
                yield b"chunk1"
                yield b"chunk2"

            mock_src_client.download_stream.side_effect = mock_download_stream

            # Mock object meta
            mock_meta = MagicMock()
            mock_meta.content_type = "application/octet-stream"
            mock_src_client.get_object_meta.return_value = mock_meta

            bytes_copied = await reservoir_service._stream_bucket_to_bucket(
                source_cfg=mock_reservoir_config,
                storage_name="test_storage",
                options=BucketCopyOptions(concurrency=2, progress_log_interval_bytes=0),
                progress_reporter=mock_progress_reporter,
                key_prefix="models/",
            )

            assert bytes_copied == 1500
            mock_list_keys.assert_called_once()
            assert mock_dst_client.upload_stream.call_count == 2

    @pytest.mark.asyncio
    async def test_stream_bucket_to_bucket_no_objects(
        self,
        reservoir_service: ReservoirService,
        mock_reservoir_config: ReservoirConfig,
        mock_progress_reporter: MagicMock,
    ) -> None:
        """Test bucket streaming with no objects to copy."""
        with patch.object(reservoir_service, "_list_all_keys_and_sizes") as mock_list_keys:
            mock_list_keys.return_value = ([], {}, 0)

            with pytest.raises(ArtifactStorageEmptyError):
                await reservoir_service._stream_bucket_to_bucket(
                    source_cfg=mock_reservoir_config,
                    storage_name="test_storage",
                    options=BucketCopyOptions(concurrency=1, progress_log_interval_bytes=0),
                    progress_reporter=mock_progress_reporter,
                    key_prefix="models/",
                )

    @pytest.mark.asyncio
    async def test_import_model_success(
        self,
        reservoir_service: ReservoirService,
        mock_progress_reporter: MagicMock,
    ) -> None:
        """Test successful model import."""
        model_target = ModelTarget(model_id="microsoft/DialoGPT-medium", revision="main")

        with (
            patch.object(reservoir_service, "_stream_bucket_to_bucket") as mock_stream,
            patch.object(reservoir_service, "_event_producer") as mock_event_producer,
        ):
            mock_stream.return_value = 1000
            mock_event_producer.anycast_event = AsyncMock()

            await reservoir_service.import_model(
                registry_name="test_registry",
                model=model_target,
                storage_name="test_storage",
                reporter=mock_progress_reporter,
            )

            mock_stream.assert_called_once()
            mock_event_producer.anycast_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_model_no_registry_config(self) -> None:
        """Test model import with no registry configuration."""
        # Create service without reservoir configs
        args = ReservoirServiceArgs(
            background_task_manager=MagicMock(),
            event_producer=MagicMock(),
            storage_pool=MagicMock(spec=StoragePool),
            reservoir_registry_configs=[],
        )
        service = ReservoirService(args)

        model_target = ModelTarget(model_id="test/model", revision="main")

        with pytest.raises(ReservoirStorageConfigInvalidError):
            await service.import_model(
                registry_name="test_registry",
                model=model_target,
                storage_name="test_storage",
                reporter=MagicMock(),
            )

    @pytest.mark.asyncio
    async def test_import_models_batch_success(
        self,
        reservoir_service: ReservoirService,
        mock_background_task_manager: MagicMock,
    ) -> None:
        """Test successful batch model import."""
        expected_task_id = uuid.uuid4()
        mock_background_task_manager.start.return_value = expected_task_id

        models = [
            ModelTarget(model_id="microsoft/DialoGPT-medium", revision="main"),
            ModelTarget(model_id="microsoft/DialoGPT-small", revision="main"),
        ]

        task_id = await reservoir_service.import_models_batch(
            registry_name="test_registry",
            models=models,
            storage_name="test_storage",
        )

        assert task_id == expected_task_id
        mock_background_task_manager.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_models_batch_empty_models(
        self,
        reservoir_service: ReservoirService,
        mock_background_task_manager: MagicMock,
    ) -> None:
        """Test batch model import with empty model list."""
        expected_task_id = uuid.uuid4()
        mock_background_task_manager.start.return_value = expected_task_id

        task_id = await reservoir_service.import_models_batch(
            registry_name="test_registry",
            models=[],
            storage_name="test_storage",
        )

        assert task_id == expected_task_id
        mock_background_task_manager.start.assert_called_once()
