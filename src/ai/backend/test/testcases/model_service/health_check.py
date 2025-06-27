import asyncio
from typing import override

import aiohttp

from ai.backend.test.contexts.model_service import (
    CreatedModelServiceEndpointMetaContext,
    CreatedModelServiceTokenContext,
)
from ai.backend.test.templates.template import TestCode

_ENDPOINT_HEALTH_CHECK_TIMEOUT = 20


# TODO: Consider health check points for each runtime variant (See MODEL_SERVICE_RUNTIME_PROFILES)
def _make_endpoint_health_check_url(endpoint_url: str) -> str:
    """
    Constructs the health check URL for the given endpoint URL.
    """
    return f"{endpoint_url}/health"


class EndpointHealthCheck(TestCode):
    _expected_status_codes: set[int]

    def __init__(self, expected_status_codes: set[int]) -> None:
        super().__init__()
        self._expected_status_codes = expected_status_codes

    @override
    async def test(self) -> None:
        service_meta = CreatedModelServiceEndpointMetaContext.current()
        health_check_url = _make_endpoint_health_check_url(service_meta.endpoint_url)

        async with aiohttp.ClientSession() as http_sess:
            resp = await asyncio.wait_for(
                http_sess.get(health_check_url), timeout=_ENDPOINT_HEALTH_CHECK_TIMEOUT
            )

            assert resp.status in self._expected_status_codes, (
                f"Service endpoint health check failed with status: {resp.status}, expected {self._expected_status_codes}"
            )


class EndpointHealthCheckWithToken(TestCode):
    _expected_status_codes: set[int]

    def __init__(self, expected_status_codes: set[int]) -> None:
        super().__init__()
        self._expected_status_codes = expected_status_codes

    @override
    async def test(self) -> None:
        service_meta = CreatedModelServiceEndpointMetaContext.current()
        health_check_url = _make_endpoint_health_check_url(service_meta.endpoint_url)

        token = CreatedModelServiceTokenContext.current()
        headers = {"Authorization": f"Bearer {token}"}

        async with aiohttp.ClientSession() as http_sess:
            resp = await asyncio.wait_for(
                http_sess.get(health_check_url, headers=headers),
                timeout=_ENDPOINT_HEALTH_CHECK_TIMEOUT,
            )

            assert resp.status in self._expected_status_codes, (
                f"Service endpoint health check failed with status: {resp.status}, expected {self._expected_status_codes}"
            )
