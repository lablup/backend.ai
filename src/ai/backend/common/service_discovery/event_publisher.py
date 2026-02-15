"""Event-based service discovery publisher.

Provides a reusable helper class for components to publish
ServiceRegisteredEvent and ServiceDeregisteredEvent via EventProducer.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from ai.backend.common.configs.service_discovery import ServiceDiscoveryConfig
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.service_discovery.anycast import (
    ServiceDeregisteredEvent,
    ServiceEndpointInfo,
    ServiceRegisteredEvent,
)
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ServiceDiscoveryEventPublisher",)


class ServiceDiscoveryEventPublisher:
    """Builds and publishes SD events from ServiceDiscoveryConfig.

    Each component creates an instance with its config and EventProducer,
    then calls start() to begin heartbeat publishing and stop() on shutdown.
    """

    _event_producer: EventProducer
    _config: ServiceDiscoveryConfig
    _component_version: str
    _startup_time: datetime
    _heartbeat_task: asyncio.Task[None] | None
    _stopped: bool

    def __init__(
        self,
        event_producer: EventProducer,
        config: ServiceDiscoveryConfig,
        component_version: str,
        startup_time: datetime,
    ) -> None:
        self._event_producer = event_producer
        self._config = config
        self._component_version = component_version
        self._startup_time = startup_time
        self._heartbeat_task = None
        self._stopped = False

    def _build_registered_event(self) -> ServiceRegisteredEvent:
        endpoints = [
            ServiceEndpointInfo(
                role=ep.role,
                scope=ep.scope,
                address=ep.address,
                port=ep.port,
                protocol=ep.protocol,
                metadata=ep.metadata,
            )
            for ep in self._config.endpoints
        ]
        return ServiceRegisteredEvent(
            instance_id=self._config.instance_id or "",
            service_group=self._config.service_group or "",
            display_name=self._config.display_name or "",
            version=self._component_version,
            labels=self._config.extra_labels,
            endpoints=endpoints,
            startup_time=self._startup_time,
            config_hash="",
        )

    def _build_deregistered_event(self) -> ServiceDeregisteredEvent:
        return ServiceDeregisteredEvent(
            instance_id=self._config.instance_id or "",
            service_group=self._config.service_group or "",
        )

    async def publish_registered(self) -> None:
        """Build and publish ServiceRegisteredEvent."""
        event = self._build_registered_event()
        await self._event_producer.anycast_event(event)
        log.debug(
            "Published ServiceRegisteredEvent for {}/{}",
            event.service_group,
            event.instance_id,
        )

    async def publish_deregistered(self) -> None:
        """Build and publish ServiceDeregisteredEvent."""
        event = self._build_deregistered_event()
        await self._event_producer.anycast_event(event)
        log.debug(
            "Published ServiceDeregisteredEvent for {}/{}",
            event.service_group,
            event.instance_id,
        )

    async def _heartbeat_loop(self, interval: int) -> None:
        """Periodically re-publish ServiceRegisteredEvent as a heartbeat."""
        while not self._stopped:
            try:
                await asyncio.sleep(interval)
                if not self._stopped:
                    await self.publish_registered()
            except asyncio.CancelledError:
                break
            except Exception:
                log.exception("Error publishing SD heartbeat")

    async def start(self, heartbeat_interval: int = 60) -> None:
        """Publish initial registration and start periodic heartbeat loop."""
        await self.publish_registered()
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(heartbeat_interval),
        )

    async def stop(self) -> None:
        """Stop heartbeat loop and publish deregistered event."""
        self._stopped = True
        if self._heartbeat_task is not None and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        try:
            await self.publish_deregistered()
        except Exception:
            log.exception("Error publishing SD deregistration")
