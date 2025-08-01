"""Tests for HuggingFace client implementation."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.storage.client.huggingface import HuggingFaceClient, create_huggingface_client
from ai.backend.storage.services.artifact_scanner.model.huggingface import (
    FileInfo,
    HuggingFaceAPIError,
    HuggingFaceModelNotFoundError,
    ModelInfo,
)


class TestHuggingFaceClient:
    """Test cases for HuggingFaceClient."""

    @pytest.fixture
    def client(self):
        """Create a HuggingFace client instance for testing."""
        return HuggingFaceClient()

    @pytest.fixture
    def authenticated_client(self):
        """Create an authenticated HuggingFace client instance for testing."""
        return HuggingFaceClient(token="test_token")

    @pytest.fixture
    def sample_model_info(self):
        """Sample ModelInfo for testing."""
        return ModelInfo(
            id="microsoft/DialoGPT-medium",
            name="DialoGPT-medium",
            author="microsoft",
            tags=["conversational", "pytorch", "transformers"],
            pipeline_tag="text-generation",
            downloads=100000,
            likes=500,
            created_at="2023-01-01T00:00:00Z",
            last_modified="2023-06-01T00:00:00Z",
            files=[
                FileInfo(
                    path="config.json",
                    size=1024,
                    type="file",
                    download_url="https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json",
                ),
                FileInfo(
                    path="pytorch_model.bin",
                    size=335000000,
                    type="file",
                    download_url="https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/pytorch_model.bin",
                ),
            ],
        )

    @pytest.fixture
    def sample_file_info(self):
        """Sample FileInfo for testing."""
        return FileInfo(
            path="config.json",
            size=1024,
            type="file",
            download_url="https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json",
        )

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with and without token."""
        # Test without token
        client = HuggingFaceClient()
        assert client.token is None
        assert client.service is not None
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert client.timeout == 30.0
        assert not client._closed

        # Test with token and custom settings
        client_with_token = HuggingFaceClient(
            token="test_token", max_retries=5, retry_delay=2.0, timeout=60.0
        )
        assert client_with_token.token == "test_token"
        assert client_with_token.service is not None
        assert client_with_token.max_retries == 5
        assert client_with_token.retry_delay == 2.0
        assert client_with_token.timeout == 60.0

    @pytest.mark.asyncio
    async def test_async_context_manager(self, client):
        """Test client as async context manager."""
        async with client as ctx_client:
            assert ctx_client is client
            assert not client._closed

        # After context manager, client should be closed
        assert client._closed

    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test manual client closing."""
        assert not client._closed

        await client.close()

        assert client._closed

    @pytest.mark.asyncio
    async def test_operations_on_closed_client(self, client):
        """Test that operations fail on closed client."""
        await client.close()

        with pytest.raises(RuntimeError, match="Operation attempted on closed HuggingFaceClient"):
            await client.list_models()

        with pytest.raises(RuntimeError, match="Operation attempted on closed HuggingFaceClient"):
            await client.get_model("test/model")

        with pytest.raises(RuntimeError, match="Operation attempted on closed HuggingFaceClient"):
            await client.search_models("test")

    @pytest.mark.asyncio
    async def test_reuse_closed_client_context_manager(self, client):
        """Test that closed client cannot be reused as context manager."""
        await client.close()

        with pytest.raises(RuntimeError, match="Cannot reuse closed HuggingFaceClient"):
            async with client:
                pass

    @pytest.mark.asyncio
    async def test_list_models_success(self, client, sample_model_info):
        """Test successful model listing."""
        with patch.object(client.service, "list_models", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [sample_model_info]

            result = await client.list_models(limit=5, search="DialoGPT", sort="downloads")

            assert len(result) == 1
            assert result[0].id == "microsoft/DialoGPT-medium"
            assert result[0].name == "DialoGPT-medium"
            mock_list.assert_called_once_with(limit=5, search="DialoGPT", sort="downloads")

    @pytest.mark.asyncio
    async def test_list_models_api_error(self, client):
        """Test model listing with API error."""
        with patch.object(client.service, "list_models", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = HuggingFaceAPIError("API request failed")

            with pytest.raises(HuggingFaceAPIError, match="API request failed"):
                await client.list_models()

    @pytest.mark.asyncio
    async def test_get_model_success(self, client, sample_model_info):
        """Test successful model retrieval."""
        with patch.object(client.service, "get_model", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_model_info

            result = await client.get_model("microsoft/DialoGPT-medium")

            assert result.id == "microsoft/DialoGPT-medium"
            assert result.file_count == 2
            mock_get.assert_called_once_with("microsoft/DialoGPT-medium")

    @pytest.mark.asyncio
    async def test_get_model_not_found(self, client):
        """Test model retrieval with model not found error."""
        with patch.object(client.service, "get_model", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = HuggingFaceModelNotFoundError("Model not found")

            with pytest.raises(HuggingFaceModelNotFoundError, match="Model not found"):
                await client.get_model("nonexistent/model")

    @pytest.mark.asyncio
    async def test_list_model_files_success(self, client, sample_file_info):
        """Test successful model file listing."""
        with patch.object(
            client.service, "list_model_files", new_callable=AsyncMock
        ) as mock_list_files:
            mock_list_files.return_value = [sample_file_info]

            result = await client.list_model_files("microsoft/DialoGPT-medium")

            assert len(result) == 1
            assert result[0].path == "config.json"
            assert result[0].size == 1024
            mock_list_files.assert_called_once_with("microsoft/DialoGPT-medium")

    @pytest.mark.asyncio
    async def test_get_download_url_success(self, client):
        """Test successful download URL generation."""
        expected_url = "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"

        with patch.object(
            client.service, "get_download_url", new_callable=AsyncMock
        ) as mock_get_url:
            mock_get_url.return_value = expected_url

            result = await client.get_download_url("microsoft/DialoGPT-medium", "config.json")

            assert result == expected_url
            mock_get_url.assert_called_once_with("microsoft/DialoGPT-medium", "config.json")

    @pytest.mark.asyncio
    async def test_search_models(self, client, sample_model_info):
        """Test model search functionality."""
        with patch.object(client, "list_models", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [sample_model_info]

            result = await client.search_models("conversational", limit=5)

            assert len(result) == 1
            assert result[0].id == "microsoft/DialoGPT-medium"
            mock_list.assert_called_once_with(limit=5, search="conversational", sort="downloads")

    @pytest.mark.asyncio
    async def test_get_popular_models(self, client, sample_model_info):
        """Test getting popular models."""
        with patch.object(client, "list_models", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [sample_model_info]

            result = await client.get_popular_models(limit=10)

            assert len(result) == 1
            mock_list.assert_called_once_with(limit=10, sort="downloads")

    @pytest.mark.asyncio
    async def test_get_trending_models(self, client, sample_model_info):
        """Test getting trending models."""
        with patch.object(client, "list_models", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [sample_model_info]

            result = await client.get_trending_models(limit=15)

            assert len(result) == 1
            mock_list.assert_called_once_with(limit=15, sort="likes")

    @pytest.mark.asyncio
    async def test_authenticated_client_operations(self, authenticated_client, sample_model_info):
        """Test that authenticated client passes token correctly."""
        assert authenticated_client.token == "test_token"

        with patch.object(
            authenticated_client.service, "list_models", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = [sample_model_info]

            await authenticated_client.list_models()

            # Verify the service was created with the token
            assert authenticated_client.service.scanner.token == "test_token"


class TestHuggingFaceClientRetryLogic:
    """Test cases for retry logic and error handling."""

    @pytest.fixture
    def client_with_short_timeout(self):
        """Create client with short timeout for testing."""
        return HuggingFaceClient(max_retries=2, retry_delay=0.1, timeout=0.1)

    @pytest.mark.asyncio
    async def test_retry_on_api_error(self, client_with_short_timeout):
        """Test retry logic on API errors."""
        call_count = 0

        async def mock_service_method(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times
                raise HuggingFaceAPIError("Temporary API error")
            return [ModelInfo(id="test/model", name="model")]

        with patch.object(
            client_with_short_timeout.service, "list_models", side_effect=mock_service_method
        ):
            result = await client_with_short_timeout.list_models()

            assert len(result) == 1
            assert call_count == 3  # Should have retried twice before succeeding

    @pytest.mark.asyncio
    async def test_no_retry_on_model_not_found(self, client_with_short_timeout):
        """Test that ModelNotFoundError doesn't trigger retries."""
        call_count = 0

        async def mock_service_method(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise HuggingFaceModelNotFoundError("Model not found")

        with patch.object(
            client_with_short_timeout.service, "get_model", side_effect=mock_service_method
        ):
            with pytest.raises(HuggingFaceModelNotFoundError):
                await client_with_short_timeout.get_model("nonexistent/model")

            assert call_count == 1  # Should not have retried

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client_with_short_timeout):
        """Test timeout handling."""

        async def slow_service_method(*args, **kwargs):
            await asyncio.sleep(1.0)  # Longer than timeout
            return []

        with patch.object(
            client_with_short_timeout.service, "list_models", side_effect=slow_service_method
        ):
            with pytest.raises((asyncio.TimeoutError, HuggingFaceAPIError)):
                await client_with_short_timeout.list_models()

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, client_with_short_timeout):
        """Test exponential backoff in retry logic."""
        call_times = []

        async def mock_service_method(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            raise HuggingFaceAPIError("Always fail")

        with patch.object(
            client_with_short_timeout.service, "list_models", side_effect=mock_service_method
        ):
            with pytest.raises(HuggingFaceAPIError):
                await client_with_short_timeout.list_models()

            # Should have made 3 attempts (initial + 2 retries)
            assert len(call_times) == 3

            # Check that delays increased (allowing for some timing variance)
            if len(call_times) >= 2:
                first_delay = call_times[1] - call_times[0]
                second_delay = call_times[2] - call_times[1]
                # Second delay should be roughly twice the first (exponential backoff)
                assert second_delay > first_delay

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client_with_short_timeout):
        """Test behavior when max retries is exceeded."""
        call_count = 0

        async def mock_service_method(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise HuggingFaceAPIError("Always fail")

        with patch.object(
            client_with_short_timeout.service, "list_models", side_effect=mock_service_method
        ):
            with pytest.raises(HuggingFaceAPIError):
                await client_with_short_timeout.list_models()

            # Should have made initial attempt + max_retries attempts
            assert call_count == 3  # 1 + 2 retries


class TestHuggingFaceClientPerformance:
    """Performance and stress tests for HuggingFace client."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        client = HuggingFaceClient()

        async def mock_service_method(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate some processing time
            return [ModelInfo(id="test/model", name="model")]

        with patch.object(client.service, "list_models", side_effect=mock_service_method):
            # Create multiple concurrent requests
            tasks = [client.list_models() for _ in range(5)]

            start_time = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()

            # All requests should succeed
            assert len(results) == 5
            assert all(len(result) == 1 for result in results)

            # Should complete in roughly parallel time (not sequential)
            # Allow some overhead for test execution
            assert end_time - start_time < 0.5  # Should be much less than 5 * 0.1 = 0.5s

        await client.close()

    @pytest.mark.asyncio
    async def test_resource_cleanup_on_exception(self):
        """Test that resources are properly cleaned up on exceptions."""
        client = HuggingFaceClient()

        async def failing_service_method(*args, **kwargs):
            raise Exception("Unexpected error")

        with patch.object(client.service, "list_models", side_effect=failing_service_method):
            with pytest.raises(Exception):
                await client.list_models()

            # Client should still be usable after an exception
            assert not client._closed

        await client.close()


class TestHuggingFaceClientIntegration:
    """Integration tests for HuggingFace client."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_api_list_models(self):
        """Test listing models against real HuggingFace API."""
        async with HuggingFaceClient() as client:
            models = await client.list_models(limit=3)

            assert len(models) <= 3
            for model in models:
                assert model.id
                assert model.name
                assert model.downloads >= 0
                assert model.likes >= 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_api_get_model(self):
        """Test getting a specific model against real HuggingFace API."""
        async with HuggingFaceClient() as client:
            model = await client.get_model("microsoft/DialoGPT-small")

            assert model.id == "microsoft/DialoGPT-small"
            assert model.name == "DialoGPT-small"
            assert model.author == "microsoft"
            assert len(model.files) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_api_nonexistent_model(self):
        """Test getting a nonexistent model against real HuggingFace API."""
        async with HuggingFaceClient() as client:
            with pytest.raises(HuggingFaceModelNotFoundError):
                await client.get_model("nonexistent/definitely-does-not-exist")


class TestCreateHuggingFaceClient:
    """Test the convenience function for creating clients."""

    @pytest.mark.asyncio
    async def test_create_client_without_token(self):
        """Test creating client without token."""
        client = await create_huggingface_client()
        assert isinstance(client, HuggingFaceClient)
        assert client.token is None

    @pytest.mark.asyncio
    async def test_create_client_with_token(self):
        """Test creating client with token."""
        client = await create_huggingface_client(token="test_token")
        assert isinstance(client, HuggingFaceClient)
        assert client.token == "test_token"
