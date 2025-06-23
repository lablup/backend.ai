import asyncio
from typing import override

import aiohttp

from ai.backend.test.contexts.model_service import CreatedModelServiceEndpointContext
from ai.backend.test.templates.template import TestCode

_ENDPOINT_HEALTH_CHECK_TIMEOUT = 10


class EndpointHealthCheck(TestCode):
    def __init__(self) -> None:
        super().__init__()

    @override
    async def test(self) -> None:
        endpoint_url = CreatedModelServiceEndpointContext.current()
        health_check_url = endpoint_url + "/health"

        async with aiohttp.ClientSession() as http_sess:
            resp = await asyncio.wait_for(
                http_sess.get(health_check_url), timeout=_ENDPOINT_HEALTH_CHECK_TIMEOUT
            )

            assert resp.status // 100 == 2, (
                f"Service endpoint health check failed with status: {resp.status}"
            )
