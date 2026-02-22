from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.data.service_catalog.types import (
    ServiceCatalogData,
    ServiceCatalogEndpointData,
)
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import execute_batch_querier
from ai.backend.manager.services.service_catalog.actions.search import (
    SearchServiceCatalogsAction,
    SearchServiceCatalogsActionResult,
)


def _row_to_data(row: ServiceCatalogRow) -> ServiceCatalogData:
    return ServiceCatalogData(
        id=row.id,
        service_group=row.service_group,
        instance_id=row.instance_id,
        display_name=row.display_name,
        version=row.version,
        labels=row.labels,
        status=row.status,
        startup_time=row.startup_time,
        registered_at=row.registered_at,
        last_heartbeat=row.last_heartbeat,
        config_hash=row.config_hash,
        endpoints=[
            ServiceCatalogEndpointData(
                id=ep.id,
                service_id=ep.service_id,
                role=ep.role,
                scope=ep.scope,
                address=ep.address,
                port=ep.port,
                protocol=ep.protocol,
                metadata=ep.metadata_,
            )
            for ep in row.endpoints
        ],
    )


@dataclass
class ServiceCatalogService:
    """Service for service catalog operations."""

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def search_service_catalogs(
        self, action: SearchServiceCatalogsAction
    ) -> SearchServiceCatalogsActionResult:
        """Search service catalog entries with batch querier pagination."""
        stmt = sa.select(ServiceCatalogRow).options(selectinload(ServiceCatalogRow.endpoints))

        async with self._db.begin_readonly_session() as session:
            result = await execute_batch_querier(session, stmt, action.querier)

        catalogs = [_row_to_data(row.ServiceCatalogRow) for row in result.rows]
        return SearchServiceCatalogsActionResult(
            data=catalogs,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
