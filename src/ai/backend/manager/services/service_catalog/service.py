from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.service_catalog.actions.search import (
    SearchServiceCatalogsAction,
    SearchServiceCatalogsActionResult,
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
        """Search service catalog entries with optional filters and pagination."""
        stmt = (
            sa.select(ServiceCatalogRow)
            .options(selectinload(ServiceCatalogRow.endpoints))
            .order_by(ServiceCatalogRow.service_group, ServiceCatalogRow.instance_id)
        )

        if action.service_group is not None:
            stmt = stmt.where(ServiceCatalogRow.service_group == action.service_group)

        if action.status is not None:
            stmt = stmt.where(ServiceCatalogRow.status == ServiceCatalogStatus(action.status))

        if action.offset is not None:
            stmt = stmt.offset(action.offset)

        if action.first is not None:
            stmt = stmt.limit(action.first)

        async with self._db.begin_readonly_session() as session:
            result = await session.execute(stmt)
            rows = list(result.scalars().all())

        return SearchServiceCatalogsActionResult(catalogs=rows)
