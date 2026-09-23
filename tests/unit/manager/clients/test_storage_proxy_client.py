from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
from aiohttp import ClientSession, ClientTimeout, web
from aiohttp.test_utils import TestClient

from ai.backend.common.configs.client import HttpTimeoutConfig
from ai.backend.common.endpoint_pool.pool import HealthyEndpointPool
from ai.backend.common.endpoint_pool.strategy import RoundRobinStrategy
from ai.backend.common.endpoint_pool.types import EndpointPoolSpec
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
from ai.backend.manager.errors.storage import StorageProxyConnectionError, StorageProxyTimeoutError

type HandlerType = Callable[[web.Request], Coroutine[Any, Any, web.Response]]
type StorageProxyClientFactory = Callable[
    [str, HandlerType], Coroutine[Any, Any, StorageProxyHTTPClient]
]


@pytest.fixture
async def storage_proxy_client_factory(
    aiohttp_client: Any,  # pytest-aiohttp plugin fixture
) -> AsyncIterator[StorageProxyClientFactory]:
    """Factory fixture to create StorageProxyHTTPClient with a mock handler."""

    pools: list[HealthyEndpointPool] = []

    async def _factory(
        endpoint_path: str,
        handler: HandlerType,
    ) -> StorageProxyHTTPClient:
        app = web.Application()
        app.router.add_get(f"/{endpoint_path}", handler)
        client: TestClient[Any] = await aiohttp_client(app)  # type: ignore[type-arg]

        pool = HealthyEndpointPool(
            endpoints=[str(client.make_url("/"))],
            spec=EndpointPoolSpec("/readyz", 3600, 1, 60, 2),
            strategy=RoundRobinStrategy(),
            probe_session_factory=lambda endpoint: ClientSession(base_url=endpoint),
            unavailable_error_factory=StorageProxyConnectionError,
        )
        pools.append(pool)
        return StorageProxyHTTPClient(
            client_session=client.session,
            args=StorageProxyClientArgs(
                endpoint_pool=pool,
                secret="test-secret",
            ),
        )

    try:
        yield _factory
    finally:
        for pool in pools:
            await pool.close()


class TestStorageProxyClient:
    async def test_client_gracefully_handle_non_json_response(
        self, storage_proxy_client_factory: StorageProxyClientFactory
    ) -> None:
        """Test that StorageProxyHTTPClient gracefully handles non-JSON error responses."""
        test_status_code = 403
        test_endpoint = "invalid-endpoint"

        async def invalid_endpoint_handler(_request: web.Request) -> web.Response:
            return web.Response(
                status=test_status_code,
                body="This is not a JSON response",
                content_type="text/plain",
            )

        storage_proxy_client = await storage_proxy_client_factory(
            test_endpoint, invalid_endpoint_handler
        )

        # Verify that non-JSON response raises PassthroughError with correct error code
        with pytest.raises(PassthroughError) as exc_info:
            await storage_proxy_client.request(
                method="GET", url=test_endpoint, request_timeout=DEFAULT_TIMEOUT
            )

        assert exc_info.value.status_code == test_status_code

        error_code = exc_info.value.error_code()
        assert error_code.domain == ErrorDomain.STORAGE_PROXY
        assert error_code.operation == ErrorOperation.REQUEST
        assert error_code.error_detail == ErrorDetail.CONTENT_TYPE_MISMATCH

    async def test_request_timeout_expiration(
        self, storage_proxy_client_factory: StorageProxyClientFactory
    ) -> None:
        """Test that request properly times out when timeout expires."""
        test_endpoint = "slow-endpoint"

        async def slow_endpoint_handler(_request: web.Request) -> web.Response:
            # Sleep for longer than the timeout
            await asyncio.sleep(2.0)
            return web.json_response({"status": "success"})

        storage_proxy_client = await storage_proxy_client_factory(
            test_endpoint, slow_endpoint_handler
        )

        # Make request with very short timeout
        timeout = ClientTimeout(total=0.1)
        with pytest.raises(StorageProxyTimeoutError) as exc_info:
            await storage_proxy_client.request(
                method="GET",
                url=test_endpoint,
                request_timeout=timeout,
            )

        assert "Request to storage proxy timed out" in str(exc_info.value)

    async def test_configured_client_timeout_causes_timeout_error(
        self, storage_proxy_client_factory: StorageProxyClientFactory
    ) -> None:
        """
        Test that configured short timeout causes timeout error when server is slow.
        Note: get_volumes is used as an arbitrary method call to test timeout behavior.
        """

        async def volumes_handler(_request: web.Request) -> web.Response:
            # Sleep for a bit to allow timeout to potentially trigger
            await asyncio.sleep(0.5)
            return web.json_response({"volumes": []})

        http_client = await storage_proxy_client_factory("volumes", volumes_handler)

        # Create manager client with custom very short timeout for get_volumes
        custom_timeout = HttpTimeoutConfig(total=0.1, sock_connect=0.05)  # type: ignore[call-arg]
        timeout_config = StorageProxyClientTimeoutConfig(get_volumes=custom_timeout)  # type: ignore[call-arg]
        manager_client = StorageProxyManagerFacingClient(
            client=http_client,
            timeout_config=timeout_config,
        )

        # The request should timeout because server sleeps for 0.5s
        with pytest.raises(StorageProxyTimeoutError):
            await manager_client.get_volumes()

    async def test_configured_client_timeout_succeeds(
        self, storage_proxy_client_factory: StorageProxyClientFactory
    ) -> None:
        """
        Test that request succeeds when configured timeout is sufficient.
        Note: get_volumes is used as an arbitrary method call to test timeout behavior.
        """

        async def volumes_handler(_request: web.Request) -> web.Response:
            # Short delay that is within timeout
            await asyncio.sleep(0.1)
            return web.json_response({"volumes": ["volume1", "volume2"]})

        http_client = await storage_proxy_client_factory("volumes", volumes_handler)

        # Create manager client with sufficient timeout for get_volumes
        custom_timeout = HttpTimeoutConfig(total=5.0, sock_connect=1.0)  # type: ignore[call-arg]
        timeout_config = StorageProxyClientTimeoutConfig(get_volumes=custom_timeout)  # type: ignore[call-arg]
        manager_client = StorageProxyManagerFacingClient(
            client=http_client,
            timeout_config=timeout_config,
        )

        # The request should succeed because timeout is sufficient
        result = await manager_client.get_volumes()
        assert result == {"volumes": ["volume1", "volume2"]}
