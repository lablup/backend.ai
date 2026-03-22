"""Query orders for deployment revision repository."""

from __future__ import annotations

from typing import cast

from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.repositories.base import QueryOrder


class RevisionOrders:
    """Query orders for revisions."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.name.asc())
        return cast(QueryOrder, DeploymentRevisionRow.name.desc())

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.created_at.asc())
        return cast(QueryOrder, DeploymentRevisionRow.created_at.desc())
