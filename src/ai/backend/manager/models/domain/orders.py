"""Query orders for domain rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryOrder

from .row import DomainRow

__all__ = ("DomainOrders",)


class DomainOrders:
    """Query orders for sorting domains."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.name.asc()
        return DomainRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.created_at.asc()
        return DomainRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.modified_at.asc()
        return DomainRow.modified_at.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.is_active.asc()
        return DomainRow.is_active.desc()

    # ==================== Project Nested Orders ====================

    @staticmethod
    def _scalar_project_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery with MIN for 1:N relationship (Domain → Project)."""
        return (
            sa.select(sa.func.min(column))
            .where(GroupRow.domain_name == DomainRow.name)
            .correlate(DomainRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        subq = DomainOrders._scalar_project_min(GroupRow.name)
        return subq.asc() if ascending else subq.desc()

    # ==================== User Nested Orders ====================

    @staticmethod
    def _scalar_user_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery with MIN for 1:N relationship (Domain → User)."""
        return (
            sa.select(sa.func.min(column))
            .where(UserRow.domain_name == DomainRow.name)
            .correlate(DomainRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        subq = DomainOrders._scalar_user_min(UserRow.username)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        subq = DomainOrders._scalar_user_min(UserRow.email)
        return subq.asc() if ascending else subq.desc()
