"""Query orders for service catalog rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.service_catalog.types import (
    OrderDirection,
    ServiceCatalogOrderField,
)
from ai.backend.manager.repositories.base import QueryOrder

from .row import ServiceCatalogRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[ServiceCatalogOrderField, _OrderColumn] = {
    ServiceCatalogOrderField.SERVICE_GROUP: ServiceCatalogRow.service_group,
    ServiceCatalogOrderField.DISPLAY_NAME: ServiceCatalogRow.display_name,
    ServiceCatalogOrderField.REGISTERED_AT: ServiceCatalogRow.registered_at,
    ServiceCatalogOrderField.LAST_HEARTBEAT: ServiceCatalogRow.last_heartbeat,
    ServiceCatalogOrderField.STATUS: ServiceCatalogRow.status,
}

DEFAULT_FORWARD_ORDER: QueryOrder = ServiceCatalogRow.registered_at.desc()
DEFAULT_BACKWARD_ORDER: QueryOrder = ServiceCatalogRow.registered_at.asc()
TIEBREAKER_ORDER: QueryOrder = ServiceCatalogRow.id.asc()


def resolve_order(field: ServiceCatalogOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
