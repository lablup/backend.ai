"""Query orders for deployment revision repository."""

from __future__ import annotations

from typing import cast

from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.repositories.base import QueryOrder


class RevisionOrders:
    """Query orders for revisions."""

    @staticmethod
    def revision_number(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.revision_number.asc())
        return cast(QueryOrder, DeploymentRevisionRow.revision_number.desc())

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.created_at.asc())
        return cast(QueryOrder, DeploymentRevisionRow.created_at.desc())
