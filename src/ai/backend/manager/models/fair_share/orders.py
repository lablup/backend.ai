"""Query orders for fair share repository."""

from __future__ import annotations

from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryOrder


class DomainFairShareOrders:
    """Query orders for DomainFairShareRow."""

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = DomainFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        col = DomainFairShareRow.domain_name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = DomainFairShareRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_domain_is_active(ascending: bool = True) -> QueryOrder:
        col = DomainRow.is_active
        return col.asc() if ascending else col.desc()


class ProjectFairShareOrders:
    """Query orders for ProjectFairShareRow."""

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = ProjectFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = ProjectFairShareRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        col = GroupRow.name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_project_is_active(ascending: bool = True) -> QueryOrder:
        col = GroupRow.is_active
        return col.asc() if ascending else col.desc()


class UserFairShareOrders:
    """Query orders for UserFairShareRow."""

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = UserFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = UserFairShareRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        col = UserRow.username
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        col = UserRow.email
        return col.asc() if ascending else col.desc()


class RGDomainFairShareOrders:
    """Query orders for rg-scoped domain fair share queries.

    Uses DomainRow (base table) columns for reliable sorting,
    and DomainFairShareRow (LEFT JOIN'd) for fair-share-specific ordering.
    """

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        col = DomainRow.name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = DomainFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = DomainFairShareRow.created_at
        return col.asc() if ascending else col.desc()


class RGProjectFairShareOrders:
    """Query orders for rg-scoped project fair share queries.

    Uses ProjectFairShareRow (LEFT JOIN'd) for fair-share-specific ordering.
    """

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = ProjectFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = ProjectFairShareRow.created_at
        return col.asc() if ascending else col.desc()


class RGUserFairShareOrders:
    """Query orders for rg-scoped user fair share queries.

    Uses UserFairShareRow (LEFT JOIN'd) for fair-share-specific ordering.
    """

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = UserFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = UserFairShareRow.created_at
        return col.asc() if ascending else col.desc()
