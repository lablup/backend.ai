"""Event-based service discovery publisher.

Provides a reusable helper class for components to publish
ServiceRegisteredEvent and ServiceDeregisteredEvent via EventProducer.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Final, override

from ai.backend.common.configs.service_discovery import ServiceDiscoveryConfig
from ai.backend.common.cron import LocalCron, PeriodicTask
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.service_discovery.anycast import (
    ServiceDeregisteredEvent,
    ServiceEndpointInfo,
    ServiceRegisteredEvent,
)
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ServiceDiscoveryEventPublisher",)


class _ServiceDiscoveryHeartbeatTask(PeriodicTask):
    """Periodically re-publish ServiceRegisteredEvent as a heartbeat."""

    _publisher: Final[ServiceDiscoveryEventPublisher]
    _interval: Final[float]

    def __init__(self, publisher: ServiceDiscoveryEventPublisher, interval: float) -> None:
        self._publisher = publisher
        self._interval = interval

    @property
    @override
    def name(self) -> str:
        return "service_discovery_heartbeat"

    @property
    @override
    def interval(self) -> float:
        return self._interval

    @property
    @override
    def initial_delay(self) -> float:
        # The original loop slept for `interval` before publishing the first
        # heartbeat (the initial registration is published by start() directly).
        return self._interval

    @override
    async def run(self) -> None:
        await self._publisher.publish_registered()


class ServiceDiscoveryEventPublisher:
    """Builds and publishes SD events from ServiceDiscoveryConfig.

    Each component creates an instance with its config and EventProducer,
    then calls start() to begin heartbeat publishing and stop() on shutdown.
    """

    _event_producer: EventProducer
    _config: ServiceDiscoveryConfig
    _component_version: str
    _startup_time: datetime
    _local_cron: LocalCron

    def __init__(
        self,
        event_producer: EventProducer,
        config: ServiceDiscoveryConfig,
        component_version: str,
        startup_time: datetime,
        heartbeat_interval: float = 60.0,
    ) -> None:
        self._event_producer = event_producer
        self._config = config
        self._component_version = component_version
        self._startup_time = startup_time
        self._local_cron = LocalCron([
            _ServiceDiscoveryHeartbeatTask(self, heartbeat_interval),
        ])

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

    async def start(self) -> None:
        """Publish initial registration and start periodic heartbeat loop."""
        await self.publish_registered()
        await self._local_cron.start()

    async def stop(self) -> None:
        """Stop heartbeat loop and publish deregistered event."""
        await self._local_cron.stop()
        try:
            await self.publish_deregistered()
        except Exception:
            log.exception("Error publishing SD deregistration")
