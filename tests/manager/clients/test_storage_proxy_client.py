import pytest
from aiohttp import web

from ai.backend.common.exception import ErrorDetail, ErrorDomain, ErrorOperation, PassthroughError
from ai.backend.manager.clients.storage_proxy.base import (
    StorageProxyClientArgs,
    StorageProxyHTTPClient,
)


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
            await storage_proxy_client.request(method="GET", url=test_endpoint)

        assert exc_info.value.status_code == test_status_code

        error_code = exc_info.value.error_code()
        assert error_code.domain == ErrorDomain.STORAGE_PROXY
        assert error_code.operation == ErrorOperation.REQUEST
        assert error_code.error_detail == ErrorDetail.CONTENT_TYPE_MISMATCH
