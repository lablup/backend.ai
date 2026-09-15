"""Query orders for vfolder rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.dto.manager.v2.vfolder.types import OrderDirection, VFolderOrderField
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.user.queries import user_scope_shares
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

from .row import VFolderRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[VFolderOrderField, _OrderColumn] = {
    VFolderOrderField.NAME: VFolderRow.name,
    VFolderOrderField.CREATED_AT: VFolderRow.created_at,
    VFolderOrderField.STATUS: VFolderRow.status,
    VFolderOrderField.USAGE_MODE: VFolderRow.usage_mode,
    VFolderOrderField.HOST: VFolderRow.host,
}

DEFAULT_FORWARD_ORDER: QueryOrder = VFolderRow.created_at.desc()
DEFAULT_BACKWARD_ORDER: QueryOrder = VFolderRow.created_at.asc()
TIEBREAKER_ORDER: QueryOrder = VFolderRow.id.asc()


class VFolderOrders:
    """Query orders for vfolders."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.created_at.asc()
        return VFolderRow.created_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.id.asc()
        return VFolderRow.id.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.name.asc()
        return VFolderRow.name.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.status.asc()
        return VFolderRow.status.desc()

    @staticmethod
    def usage_mode(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.usage_mode.asc()
        return VFolderRow.usage_mode.desc()

    @staticmethod
    def host(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.host.asc()
        return VFolderRow.host.desc()

    @staticmethod
    def project_first(project_id: ProjectID) -> QueryOrder:
        """The folders the project reaches, ahead of the rest."""
        return scope_membership_exists(
            ProjectEntityType(), project_id, VFolderEntityType(), VFolderRow.id
        ).desc()

    @staticmethod
    def shared_last(user_id: UserID) -> QueryOrder:
        """The folders shared to the user, behind the rest."""
        return user_scope_shares(user_id, VFolderEntityType(), VFolderRow.id).asc()


def resolve_order(field: VFolderOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
