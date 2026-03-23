"""Query orders for artifact repository."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.artifact.types import ArtifactOrderField, OrderDirection
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.repositories.base import QueryOrder

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[ArtifactOrderField, _OrderColumn] = {
    ArtifactOrderField.NAME: ArtifactRow.name,
    ArtifactOrderField.TYPE: ArtifactRow.type,
    ArtifactOrderField.SCANNED_AT: ArtifactRow.scanned_at,
    ArtifactOrderField.UPDATED_AT: ArtifactRow.updated_at,
}

DEFAULT_FORWARD_ORDER: QueryOrder = ArtifactRow.id.desc()
TIEBREAKER_ORDER: QueryOrder = ArtifactRow.id.asc()


def resolve_order(field: ArtifactOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()


class ArtifactOrders:
    """Query orders for artifacts."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.name.asc()
        return ArtifactRow.name.desc()

    @staticmethod
    def type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.type.asc()
        return ArtifactRow.type.desc()

    @staticmethod
    def scanned_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.scanned_at.asc()
        return ArtifactRow.scanned_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.updated_at.asc()
        return ArtifactRow.updated_at.desc()
