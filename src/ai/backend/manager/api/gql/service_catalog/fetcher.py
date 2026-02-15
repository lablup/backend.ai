"""Fetcher for service catalog GraphQL queries.

Direct SQLAlchemy queries against service_catalog tables.
No service/repository layer needed since this is read-only admin query.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .types import ServiceCatalogFilterGQL, ServiceCatalogGQL

__all__ = ("fetch_service_catalogs",)


async def fetch_service_catalogs(
    db: ExtendedAsyncSAEngine,
    filter: ServiceCatalogFilterGQL | None = None,
    first: int | None = None,
    offset: int | None = None,
) -> list[ServiceCatalogGQL]:
    """Fetch service catalogs with optional filters and pagination."""
    stmt = (
        sa.select(ServiceCatalogRow)
        .options(selectinload(ServiceCatalogRow.endpoints))
        .order_by(ServiceCatalogRow.service_group, ServiceCatalogRow.instance_id)
    )

    if filter is not None:
        conditions = filter.build_sa_conditions()
        for cond in conditions:
            stmt = stmt.where(cond)

    if offset is not None:
        stmt = stmt.offset(offset)

    if first is not None:
        stmt = stmt.limit(first)

    async with db.begin_readonly_session() as session:
        result = await session.execute(stmt)
        rows = result.scalars().all()

    return [ServiceCatalogGQL.from_row(row) for row in rows]
