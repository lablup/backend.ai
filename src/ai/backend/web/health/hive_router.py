from __future__ import annotations

from http import HTTPMethod

import aiohttp

from ai.backend.common.health.checkers.http import HttpHealthChecker


class HiveRouterHealthChecker(HttpHealthChecker):
    """
    Health checker for Hive Router (Apollo Router) endpoint.

    This is a specialized HTTP health checker that checks the /health
    endpoint of the Hive Router (Apollo Router).
    """

    def __init__(
        self,
        url: str,
        session: aiohttp.ClientSession,
        timeout: float = 5.0,
    ) -> None:
        """
        Initialize HiveRouterHealthChecker.

        Args:
            url: Base URL of the Hive Router (without /health path)
            session: aiohttp ClientSession to use for requests
            timeout: Timeout in seconds for the health check
        """
        # Ensure URL ends with /health
        health_url = url.rstrip("/") + "/health"
        super().__init__(
            url=health_url,
            session=session,
            method=HTTPMethod.GET,
            expected_status_codes=[200],
            timeout=timeout,
        )
