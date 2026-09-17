"""Event handler for service catalog events.

Consumes ServiceRegisteredEvent and ServiceDeregisteredEvent,
persisting service catalog data to the database.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.events.event_types.service_discovery.anycast import (
    DoSweepStaleServicesEvent,
    ServiceDeregisteredEvent,
    ServiceRegisteredEvent,
)
from ai.backend.common.types import AgentId, ServiceCatalogStatus
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.service_catalog.creators import ServiceCatalogEndpointCreator
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.service_catalog.upserters import ServiceCatalogUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.service_catalog.repository import ServiceCatalogRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ServiceCatalogEventHandler:
    """Handles SD events by persisting to service_catalog tables."""

    _db: ExtendedAsyncSAEngine
    _repository: ServiceCatalogRepository

    def __init__(self, db: ExtendedAsyncSAEngine, repository: ServiceCatalogRepository) -> None:
        self._db = db
        self._repository = repository

    async def handle_registered(
        self,
        _context: None,
        _source: AgentId,
        event: ServiceRegisteredEvent,
    ) -> None:
        """Upsert the service catalog entry and replace its endpoints."""
        await self._repository.register(
            ServiceCatalogUpserter(
                service_group=event.service_group,
                instance_id=event.instance_id,
                display_name=event.display_name,
                version=event.version,
                labels=event.labels,
                startup_time=event.startup_time,
                config_hash=event.config_hash,
            ),
            [
                ServiceCatalogEndpointCreator(
                    role=ep.role,
                    scope=ep.scope,
                    address=ep.address,
                    port=ep.port,
                    protocol=ep.protocol,
                    metadata=ep.metadata,
                )
                for ep in event.endpoints
            ],
        )
        log.debug(
            "Upserted service catalog entry: {}/{}",
            event.service_group,
            event.instance_id,
        )

    async def handle_deregistered(
        self,
        _context: None,
        _source: AgentId,
        event: ServiceDeregisteredEvent,
    ) -> None:
        """Mark service as DEREGISTERED."""
        async with self._db.begin_session() as session:
            await session.execute(
                sa.update(ServiceCatalogRow)
                .where(
                    (ServiceCatalogRow.service_group == event.service_group)
                    & (ServiceCatalogRow.instance_id == event.instance_id)
                )
                .values(status=ServiceCatalogStatus.DEREGISTERED)
            )
        log.debug(
            "Deregistered service: {}/{}",
            event.service_group,
            event.instance_id,
        )

    async def handle_sweep_stale_services(
        self,
        _context: None,
        _source: AgentId,
        _event: DoSweepStaleServicesEvent,
    ) -> None:
        """Handle sweep event: mark services with stale heartbeat as UNHEALTHY."""
        await self._sweep_stale_services()

    async def _sweep_stale_services(self, threshold_minutes: int = 5) -> int:
        """Mark services with stale heartbeat as UNHEALTHY.

        Uses database server time (now() - interval) for consistency.
        Returns the number of services marked as unhealthy.
        """
        cutoff = sa.func.now() - timedelta(minutes=threshold_minutes)
        async with self._db.begin_session() as session:
            result = cast(
                CursorResult[tuple[()]],
                await session.execute(
                    sa.update(ServiceCatalogRow)
                    .where(
                        (ServiceCatalogRow.last_heartbeat < cutoff)
                        & (ServiceCatalogRow.status == ServiceCatalogStatus.HEALTHY)
                    )
                    .values(status=ServiceCatalogStatus.UNHEALTHY)
                ),
            )
            count = result.rowcount
        if count > 0:
            log.info("Marked {} stale services as UNHEALTHY", count)
        return count
