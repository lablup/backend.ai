"""Central registry for notification channel handlers."""

from __future__ import annotations

import logging
from datetime import datetime

import jinja2

from ai.backend.common.clients.http_client import ClientPool
from ai.backend.common.data.notification import NotifiableMessage, NotificationChannelType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.errors.notification import (
    InvalidNotificationChannelType,
    NotificationTemplateRenderingFailure,
)

from .channels.base import AbstractNotificationChannel
from .types import NotificationMessage, ProcessRuleParams, SendResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("NotificationCenter",)


class NotificationCenter:
    """
    Central registry for notification channel handlers.

    This class manages the available notification channel handlers and
    provides a unified interface for sending notifications through different channels.
    """

    _http_client_pool: ClientPool
    _template_env: jinja2.Environment

    def __init__(self) -> None:
        """Initialize the notification center with HTTP client pool and template environment."""
        from ai.backend.common.clients.http_client import ClientPool, tcp_client_session_factory

        self._http_client_pool = ClientPool(
            factory=tcp_client_session_factory,
            cleanup_interval_seconds=600,
        )
        self._template_env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=False,
        )

    async def close(self) -> None:
        """Close the HTTP client pool and cleanup resources."""
        await self._http_client_pool.close()

    def _create_handler(
        self,
        channel_data: NotificationChannelData,
    ) -> AbstractNotificationChannel:
        """
        Create a handler for the given channel.

        Args:
            channel_data: Channel configuration and metadata

        Returns:
            Handler instance for the channel
        """
        # Create handler based on channel type (no caching due to dynamic config changes)
        match channel_data.channel_type:
            case NotificationChannelType.WEBHOOK:
                from .channels.webhook import WebhookChannel

                return WebhookChannel(
                    http_client_pool=self._http_client_pool,
                    webhook_config=channel_data.config,
                )

        # Explicitly handle unregistered channel types
        raise InvalidNotificationChannelType(
            f"No handler registered for channel type: {channel_data.channel_type}"
        )

    async def process_rule(
        self,
        params: ProcessRuleParams,
    ) -> SendResult:
        """
        Process notification rule: render template and send notification.

        Args:
            params: Parameters for rule processing

        Returns:
            SendResult indicating success

        Raises:
            Exception: If template rendering or notification delivery fails
        """
        # Render message template
        rendered_message = self._render_template(
            params.message_template,
            params.rule_type,
            params.timestamp,
            params.notification_data,
        )

        # Create notification message
        message = NotificationMessage(
            message=rendered_message,
        )

        # Send notification through channel
        handler = self._create_handler(params.channel)
        return await handler.send(message)

    async def validate_channel(
        self,
        channel_data: NotificationChannelData,
        test_message: str,
    ) -> SendResult:
        """
        Validate a notification channel by sending a test message.

        Args:
            channel_data: Channel configuration and metadata
            test_message: Test message to send

        Returns:
            SendResult indicating success

        Raises:
            NotificationProcessingFailure: If validation fails
        """
        # Create notification message from provided test message
        message = NotificationMessage(
            message=test_message,
        )

        # Send the test message
        handler = self._create_handler(channel_data)
        return await handler.send(message)

    def _render_template(
        self,
        template_str: str,
        rule_type: str,
        timestamp: datetime,
        notification_data: NotifiableMessage,
    ) -> str:
        """Render Jinja2 template with notification event data."""
        try:
            # Convert Pydantic model to dict for template context
            data_dict = notification_data.model_dump()
            template = self._template_env.from_string(template_str)
            return template.render(
                rule_type=str(rule_type),
                timestamp=timestamp,
                data=data_dict,
                **data_dict,  # Allow direct access to data fields
            )
        except jinja2.TemplateError as e:
            log.error(
                "Failed to render notification template",
                template=template_str,
                error=str(e),
            )
            raise NotificationTemplateRenderingFailure(
                f"Failed to render template: {str(e)}"
            ) from e
