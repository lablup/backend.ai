from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import uuid4

import aiohttp
import pytest
from aioresponses import aioresponses

from ai.backend.common.contexts.request_id import with_request_id
from ai.backend.manager.clients.appproxy.client import REQUEST_ID_HDR, AppProxyClient
from ai.backend.manager.clients.appproxy.types import (
    CreateEndpointRequestBody,
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)

TEST_REQUEST_ID = "test-request-id"


class TestAppProxyClientRequestId:
    @pytest.fixture
    def request_id(self) -> Iterator[str]:
        """Set up request_id context for the test."""
        with with_request_id(TEST_REQUEST_ID):
            yield TEST_REQUEST_ID

    @pytest.fixture
    def sample_request_body(self) -> CreateEndpointRequestBody:
        """Create a sample CreateEndpointRequestBody for testing."""
        return CreateEndpointRequestBody(
            service_name="test-service",
            tags=TagsModel(
                session=SessionTagsModel(
                    user_uuid=str(uuid4()),
                    group_id=str(uuid4()),
                    domain_name="default",
                ),
                endpoint=EndpointTagsModel(
                    id=str(uuid4()),
                    runtime_variant="default",
                ),
            ),
            apps={},
            open_to_public=False,
        )

    async def test_create_endpoint_includes_request_id_header(
        self, request_id: str, sample_request_body: CreateEndpointRequestBody
    ) -> None:
        """Verify that request_id from context is included in HTTP headers."""
        endpoint_id = uuid4()
        base_url = "http://test-server"
        captured_headers: dict[str, Any] = {}

        def capture_request(url: Any, **kwargs: Any) -> None:
            captured_headers.update(kwargs.get("headers", {}))

        with aioresponses() as mock_http:
            mock_http.post(
                f"{base_url}/v2/endpoints/{endpoint_id}",
                payload={"id": str(endpoint_id)},
                callback=capture_request,
            )

            async with aiohttp.ClientSession(base_url) as session:
                appproxy_client = AppProxyClient(session, base_url, "test-token")
                await appproxy_client.create_endpoint(endpoint_id, sample_request_body)

        assert REQUEST_ID_HDR in captured_headers
        assert captured_headers[REQUEST_ID_HDR] == request_id
