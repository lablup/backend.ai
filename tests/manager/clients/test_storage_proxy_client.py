import asyncio

import pytest
from aiohttp import ClientTimeout, web

from ai.backend.common.configs.storage_proxy import TimeoutConfig
from ai.backend.common.exception import ErrorDetail, ErrorDomain, ErrorOperation, PassthroughError
from ai.backend.manager.clients.storage_proxy.base import (
    DEFAULT_TIMEOUT,
    StorageProxyClientArgs,
    StorageProxyHTTPClient,
)
from ai.backend.manager.clients.storage_proxy.manager_facing_client import (
    StorageProxyManagerFacingClient,
)
from ai.backend.manager.config.unified import StorageProxyClientTimeoutConfig
from ai.backend.manager.errors.storage import StorageProxyTimeoutError


class TestStorageProxyClient:
    @pytest.mark.asyncio
    async def test_client_gracefully_handle_non_json_response(self, aiohttp_client) -> None:
        """Test that StorageProxyHTTPClient gracefully handles non-JSON error responses."""

        # Create a handler that returns non-JSON response
        test_status_code = 403

        async def invalid_endpoint_handler(_request: web.Request) -> web.Response:
            return web.Response(
                status=test_status_code,
                body="This is not a JSON response",
                content_type="text/plain",
            )

        # Set up mock storage proxy server
        app = web.Application()
        test_endpoint = "invalid-endpoint"
        app.router.add_get(f"/{test_endpoint}", invalid_endpoint_handler)
        client = await aiohttp_client(app)

        # Create storage proxy client pointing to the mock server
        storage_proxy_client = StorageProxyHTTPClient(
            client_session=client.session,
            args=StorageProxyClientArgs(
                endpoint=client.make_url("/"),
                secret="test-secret",
            ),
        )

        # Verify that non-JSON response raises PassthroughError with correct error code
        with pytest.raises(PassthroughError) as exc_info:
            await storage_proxy_client.request(
                method="GET", url=test_endpoint, timeout=DEFAULT_TIMEOUT
            )

        assert exc_info.value.status_code == test_status_code

        error_code = exc_info.value.error_code()
        assert error_code.domain == ErrorDomain.STORAGE_PROXY
        assert error_code.operation == ErrorOperation.REQUEST
        assert error_code.error_detail == ErrorDetail.CONTENT_TYPE_MISMATCH

    @pytest.mark.asyncio
    async def test_request_timeout_expiration(self, aiohttp_client) -> None:
        """Test that request properly times out when timeout expires."""

        async def slow_endpoint_handler(_request: web.Request) -> web.Response:
            # Sleep for longer than the timeout
            await asyncio.sleep(2.0)
            return web.json_response({"status": "success"})

        # Set up mock storage proxy server
        app = web.Application()
        test_endpoint = "slow-endpoint"
        app.router.add_get(f"/{test_endpoint}", slow_endpoint_handler)
        client = await aiohttp_client(app)

        # Create storage proxy client
        storage_proxy_client = StorageProxyHTTPClient(
            client_session=client.session,
            args=StorageProxyClientArgs(
                endpoint=client.make_url("/"),
                secret="test-secret",
            ),
        )

        # Make request with very short timeout
        timeout = ClientTimeout(total=0.1)
        with pytest.raises(StorageProxyTimeoutError) as exc_info:
            await storage_proxy_client.request(
                method="GET",
                url=test_endpoint,
                timeout=timeout,
            )

        assert "Request to storage proxy timed out" in str(exc_info.value)


class TestStorageProxyManagerFacingClientTimeout:
    """Tests for StorageProxyManagerFacingClient per-method timeout configuration."""

    @pytest.mark.asyncio
    async def test_get_volumes_uses_configured_timeout(self, aiohttp_client) -> None:
        """Test that get_volumes uses the configured timeout."""
        request_received_timeout: ClientTimeout | None = None

        async def volumes_handler(request: web.Request) -> web.Response:
            nonlocal request_received_timeout
            # Sleep for a bit to allow timeout to potentially trigger
            await asyncio.sleep(0.5)
            return web.json_response({"volumes": []})

        # Set up mock storage proxy server
        app = web.Application()
        app.router.add_get("/volumes", volumes_handler)
        client = await aiohttp_client(app)

        # Create storage proxy client with short timeout
        http_client = StorageProxyHTTPClient(
            client_session=client.session,
            args=StorageProxyClientArgs(
                endpoint=client.make_url("/"),
                secret="test-secret",
            ),
        )

        # Create manager client with custom very short timeout for get_volumes
        custom_timeout = TimeoutConfig(total=0.1, sock_connect=0.05)
        timeout_config = StorageProxyClientTimeoutConfig(get_volumes=custom_timeout)
        manager_client = StorageProxyManagerFacingClient(
            client=http_client,
            timeout_config=timeout_config,
        )

        # The request should timeout because server sleeps for 0.5s
        with pytest.raises(StorageProxyTimeoutError):
            await manager_client.get_volumes()

    @pytest.mark.asyncio
    async def test_list_files_uses_configured_timeout(self, aiohttp_client) -> None:
        """Test that list_files uses its own configured timeout."""

        async def list_files_handler(_request: web.Request) -> web.Response:
            await asyncio.sleep(0.5)
            return web.json_response({"items": [], "files": []})

        # Set up mock storage proxy server
        app = web.Application()
        app.router.add_post("/folder/file/list", list_files_handler)
        client = await aiohttp_client(app)

        # Create storage proxy client
        http_client = StorageProxyHTTPClient(
            client_session=client.session,
            args=StorageProxyClientArgs(
                endpoint=client.make_url("/"),
                secret="test-secret",
            ),
        )

        # Create manager client with custom timeout for list_files
        custom_timeout = TimeoutConfig(total=0.1)
        timeout_config = StorageProxyClientTimeoutConfig(list_files=custom_timeout)
        manager_client = StorageProxyManagerFacingClient(
            client=http_client,
            timeout_config=timeout_config,
        )

        # The request should timeout
        with pytest.raises(StorageProxyTimeoutError):
            await manager_client.list_files(
                volume="test-volume",
                vfid="test-vfid",
                relpath=".",
            )
