"""Query orders for user repository operations."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryOrder

__all__ = ("UserOrders",)


class UserOrders:
    """Query orders for sorting users."""

    @staticmethod
    def uuid(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.uuid.asc()
        return UserRow.uuid.desc()

    @staticmethod
    def email(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.email.asc()
        return UserRow.email.desc()

    @staticmethod
    def username(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.username.asc()
        return UserRow.username.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.created_at.asc()
        return UserRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.modified_at.asc()
        return UserRow.modified_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.status.asc()
        return UserRow.status.desc()

    @staticmethod
    def domain_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.domain_name.asc()
        return UserRow.domain_name.desc()

    # ==================== Domain Nested Orders ====================

    @staticmethod
    def _scalar_domain(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery selecting a Domain column correlated to current User."""
        return (
            sa.select(column)
            .where(DomainRow.name == UserRow.domain_name)
            .correlate(UserRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        subq = UserOrders._scalar_domain(DomainRow.name)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_created_at(ascending: bool = True) -> QueryOrder:
        subq = UserOrders._scalar_domain(DomainRow.created_at)
        return subq.asc() if ascending else subq.desc()

    # ==================== Project Nested Orders (M:N -> MIN aggregation) ====================

    @staticmethod
    def _scalar_project_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery with MIN for M:N relationship."""
        return (
            sa.select(sa.func.min(column))
            .select_from(
                sa.join(
                    AssocGroupUserRow.__table__,
                    GroupRow.__table__,
                    AssocGroupUserRow.group_id == GroupRow.id,
                )
            )
            .where(AssocGroupUserRow.user_id == UserRow.uuid)
            .correlate(UserRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        subq = UserOrders._scalar_project_min(GroupRow.name)
        return subq.asc() if ascending else subq.desc()
