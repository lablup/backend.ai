"""Query orders and pagination spec for container registry rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.container_registry.types import (
    ContainerRegistryOrderField,
    OrderDirection,
)
from ai.backend.manager.repositories.base import QueryOrder

from .row import ContainerRegistryRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[ContainerRegistryOrderField, _OrderColumn] = {
    ContainerRegistryOrderField.REGISTRY_NAME: ContainerRegistryRow.registry_name,
    ContainerRegistryOrderField.URL: ContainerRegistryRow.url,
    ContainerRegistryOrderField.TYPE: ContainerRegistryRow.type,
    ContainerRegistryOrderField.IS_GLOBAL: ContainerRegistryRow.is_global,
}

DEFAULT_FORWARD_ORDER: QueryOrder = ContainerRegistryRow.id.desc()
DEFAULT_BACKWARD_ORDER: QueryOrder = ContainerRegistryRow.id.asc()
TIEBREAKER_ORDER: QueryOrder = ContainerRegistryRow.id.asc()


def resolve_order(field: ContainerRegistryOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
