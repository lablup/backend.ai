"""Query orders for group/project repository operations."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("GroupOrders",)


class GroupOrders:
    """Query orders for sorting groups/projects."""

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.id.asc()
        return GroupRow.id.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.name.asc()
        return GroupRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.created_at.asc()
        return GroupRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.modified_at.asc()
        return GroupRow.modified_at.desc()

    @staticmethod
    def domain_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.domain_name.asc()
        return GroupRow.domain_name.desc()

    @staticmethod
    def type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.type.asc()
        return GroupRow.type.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.is_active.asc()
        return GroupRow.is_active.desc()

    # ==================== Domain Nested Orders ====================

    @staticmethod
    def _scalar_domain(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery selecting a Domain column correlated to current Group."""
        return (
            sa.select(column)
            .where(DomainRow.name == GroupRow.domain_name)
            .correlate(GroupRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_domain(DomainRow.name)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_is_active(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_domain(DomainRow.is_active)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_created_at(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_domain(DomainRow.created_at)
        return subq.asc() if ascending else subq.desc()

    # ==================== User Nested Orders ====================

    @staticmethod
    def _scalar_user_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery with MIN for M:N relationship (Group → User)."""
        return (
            sa.select(sa.func.min(column))
            .select_from(
                sa.join(
                    AssocGroupUserRow.__table__,
                    UserRow.__table__,
                    AssocGroupUserRow.user_id == UserRow.uuid,
                )
            )
            .where(AssocGroupUserRow.group_id == GroupRow.id)
            .correlate(GroupRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_user_min(UserRow.username)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_user_min(UserRow.email)
        return subq.asc() if ascending else subq.desc()
