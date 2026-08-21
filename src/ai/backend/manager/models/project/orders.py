"""Query orders for group/project repository operations."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.project import AssocGroupUserRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.user import UserRow

__all__ = ("ProjectOrders",)


class ProjectOrders:
    """Query orders for sorting groups/projects."""

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.id.asc()
        return ProjectRow.id.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.name.asc()
        return ProjectRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.created_at.asc()
        return ProjectRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.updated_at.asc()
        return ProjectRow.updated_at.desc()

    @staticmethod
    def domain_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.domain_name.asc()
        return ProjectRow.domain_name.desc()

    @staticmethod
    def type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.type.asc()
        return ProjectRow.type.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.is_active.asc()
        return ProjectRow.is_active.desc()

    # ==================== Domain Nested Orders ====================

    @staticmethod
    def _scalar_domain(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery selecting a Domain column correlated to current Group."""
        return (
            sa.select(column)
            .where(DomainRow.name == ProjectRow.domain_name)
            .correlate(ProjectRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        subq = ProjectOrders._scalar_domain(DomainRow.name)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_is_active(ascending: bool = True) -> QueryOrder:
        subq = ProjectOrders._scalar_domain(DomainRow.is_active)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_created_at(ascending: bool = True) -> QueryOrder:
        subq = ProjectOrders._scalar_domain(DomainRow.created_at)
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
            .where(AssocGroupUserRow.group_id == ProjectRow.id)
            .correlate(ProjectRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        subq = ProjectOrders._scalar_user_min(UserRow.username)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        subq = ProjectOrders._scalar_user_min(UserRow.email)
        return subq.asc() if ascending else subq.desc()
