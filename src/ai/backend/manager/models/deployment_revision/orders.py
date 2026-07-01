"""Query orders for deployment revision repository."""

from __future__ import annotations

from typing import cast

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow


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

    @staticmethod
    def resource_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.resource_group.asc())
        return cast(QueryOrder, DeploymentRevisionRow.resource_group.desc())

    @staticmethod
    def cluster_mode(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.cluster_mode.asc())
        return cast(QueryOrder, DeploymentRevisionRow.cluster_mode.desc())

    @staticmethod
    def runtime_variant_name(ascending: bool = True) -> QueryOrder:
        # Sort by the human-readable variant name, resolved through a
        # correlated subquery — the raw ``runtime_variant_id`` UUID has
        # no meaningful ordering for API consumers.
        subquery = (
            sa.select(RuntimeVariantRow.name)
            .where(RuntimeVariantRow.id == DeploymentRevisionRow.runtime_variant_id)
            .correlate(DeploymentRevisionRow)
            .scalar_subquery()
        )
        if ascending:
            return cast(QueryOrder, subquery.asc())
        return cast(QueryOrder, subquery.desc())
