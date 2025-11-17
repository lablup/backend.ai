from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime, timezone
from http import HTTPMethod

import aiohttp

from ..abc import StaticServiceHealthChecker
from ..types import API, ComponentHealthStatus, ComponentId, ServiceGroup, ServiceHealth


class HttpHealthChecker(StaticServiceHealthChecker):
    """
    Health checker for HTTP endpoints.

    Performs HTTP requests to the specified URL and considers the endpoint
    healthy if it returns one of the expected status codes.
    """

    _url: str
    _component_id: ComponentId
    _timeout: float
    _session: aiohttp.ClientSession
    _expected_status_codes: frozenset[int]
    _method: HTTPMethod

    def __init__(
        self,
        url: str,
        component_id: ComponentId,
        session: aiohttp.ClientSession,
        timeout: float = 5.0,
        expected_status_codes: Sequence[int] = (200,),
        method: HTTPMethod = HTTPMethod.GET,
    ) -> None:
        """
        Initialize HttpHealthChecker.

        Args:
            url: The HTTP endpoint URL to check
            component_id: Component identifier for this endpoint
            session: aiohttp ClientSession to use for requests
            timeout: Timeout in seconds for the health check request
            expected_status_codes: HTTP status codes considered healthy (default: [200])
            method: HTTP method to use for health check (default: GET)
        """
        self._url = url
        self._component_id = component_id
        self._timeout = timeout
        self._session = session
        self._expected_status_codes = frozenset(expected_status_codes)
        self._method = method

    @property
    def target_service_group(self) -> ServiceGroup:
        """The service group this checker monitors."""
        return API

    async def check_service(self) -> ServiceHealth:
        """
        Check HTTP endpoint health by performing an HTTP request.

        Returns:
            ServiceHealth containing status for the HTTP endpoint
        """
        check_time = datetime.now(timezone.utc)

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.request(self._method.value, self._url) as response:
                    if response.status not in self._expected_status_codes:
                        status = ComponentHealthStatus(
                            is_healthy=False,
                            last_checked_at=check_time,
                            error_message=f"HTTP {self._method} {self._url} returned status {response.status}, expected one of {sorted(self._expected_status_codes)}",
                        )
                    else:
                        status = ComponentHealthStatus(
                            is_healthy=True,
                            last_checked_at=check_time,
                            error_message=None,
                        )
        except asyncio.TimeoutError:
            status = ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=f"HTTP health check timed out after {self._timeout}s: {self._method} {self._url}",
            )
        except aiohttp.ClientError as e:
            status = ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=f"HTTP health check failed for {self._method} {self._url}: {e}",
            )
        except Exception as e:
            status = ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=f"Unexpected error during HTTP health check for {self._method} {self._url}: {e}",
            )

        return ServiceHealth(results={self._component_id: status})

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
