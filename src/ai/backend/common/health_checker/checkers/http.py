from __future__ import annotations

import asyncio
from collections.abc import Sequence
from http import HTTPMethod

import aiohttp

from ..abc import HealthChecker
from ..exceptions import HttpHealthCheckError


class HttpHealthChecker(HealthChecker):
    """
    Health checker for HTTP endpoints.

    Performs HTTP requests to the specified URL and considers the endpoint
    healthy if it returns one of the expected status codes.
    """

    _url: str
    _timeout: float
    _session: aiohttp.ClientSession
    _expected_status_codes: frozenset[int]
    _method: HTTPMethod

    def __init__(
        self,
        url: str,
        session: aiohttp.ClientSession,
        timeout: float = 5.0,
        expected_status_codes: Sequence[int] = (200,),
        method: HTTPMethod = HTTPMethod.GET,
    ) -> None:
        """
        Initialize HttpHealthChecker.

        Args:
            url: The HTTP endpoint URL to check
            session: aiohttp ClientSession to use for requests
            timeout: Timeout in seconds for the health check request
            expected_status_codes: HTTP status codes considered healthy (default: [200])
            method: HTTP method to use for health check (default: GET)
        """
        self._url = url
        self._timeout = timeout
        self._session = session
        self._expected_status_codes = frozenset(expected_status_codes)
        self._method = method

    async def check_health(self) -> None:
        """
        Check HTTP endpoint health by performing an HTTP request.

        Raises:
            HttpHealthCheckError: If the endpoint returns an unexpected status code or request fails
        """
        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.request(self._method.value, self._url) as response:
                    if response.status not in self._expected_status_codes:
                        raise HttpHealthCheckError(
                            f"HTTP health check failed: {self._method} {self._url} returned status {response.status}, "
                            f"expected one of {sorted(self._expected_status_codes)}"
                        )
        except HttpHealthCheckError:
            raise
        except asyncio.TimeoutError as e:
            raise HttpHealthCheckError(
                f"HTTP health check timed out after {self._timeout}s: {self._method} {self._url}"
            ) from e
        except aiohttp.ClientError as e:
            raise HttpHealthCheckError(
                f"HTTP health check failed for {self._method} {self._url}: {e}"
            ) from e
        except Exception as e:
            raise HttpHealthCheckError(
                f"Unexpected error during HTTP health check for {self._method} {self._url}: {e}"
            ) from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
