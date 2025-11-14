"""Webhook notification channel handler."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import aiohttp

from ai.backend.common.clients.http_client import ClientPool
from ai.backend.common.clients.http_client.client_pool import ClientKey
from ai.backend.common.data.notification import WebhookConfig
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.notification import NotificationProcessingFailure

from ...types import NotificationMessage, SendResult
from ..base import AbstractNotificationChannel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("WebhookChannel",)


class WebhookChannel(AbstractNotificationChannel):
    """Webhook notification channel handler using HTTP POST."""

    _http_client_pool: ClientPool
    _webhook_config: WebhookConfig

    def __init__(self, http_client_pool: ClientPool, webhook_config: WebhookConfig) -> None:
        """
        Initialize webhook channel handler.

        Args:
            http_client_pool: HTTP client pool for making requests
            webhook_config: Webhook configuration
        """
        self._http_client_pool = http_client_pool
        self._webhook_config = webhook_config

    async def send(
        self,
        message: NotificationMessage,
    ) -> SendResult:
        """
        Send notification via webhook HTTP POST.

        Args:
            message: Notification message to send

        Returns:
            SendResult indicating success

        Raises:
            Exception: If webhook delivery fails
        """
        webhook_url = self._webhook_config.url

        # Parse URL to get base endpoint
        parsed = urlparse(webhook_url)
        endpoint = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or "/"

        # Get client session from pool
        client_key = ClientKey(
            endpoint=endpoint,
            domain="notification",
        )
        http_session = self._http_client_pool.load_client_session(client_key)

        # Send HTTP POST request with rendered message as body
        timeout = aiohttp.ClientTimeout(total=self._webhook_config.timeout)
        headers = self._webhook_config.headers.copy()
        headers["Content-Type"] = self._webhook_config.content_type

        async with http_session.post(
            path,
            data=message.message,
            headers=headers,
            timeout=timeout,
        ) as response:
            if response.status in self._webhook_config.success_status_codes:
                log.info(
                    "Webhook sent successfully to {} (status: {})",
                    webhook_url,
                    response.status,
                )
                return SendResult(
                    message=f"Webhook sent successfully (status: {response.status})",
                )
            response_text = await response.text()
            log.warning(
                "Webhook request failed with status {}: {}",
                response.status,
                response_text[:200],
            )
            raise NotificationProcessingFailure(
                f"Webhook delivery failed with status {response.status}: {response_text[:200]}"
            )
