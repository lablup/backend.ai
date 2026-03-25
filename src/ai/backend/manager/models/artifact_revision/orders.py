"""Query orders for artifact revision repository."""

from __future__ import annotations

from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.repositories.base import QueryOrder


class ArtifactRevisionOrders:
    """Query orders for artifact revisions."""

    @staticmethod
    def version(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.version.asc()
        return ArtifactRevisionRow.version.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.status.asc()
        return ArtifactRevisionRow.status.desc()

    @staticmethod
    def size(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.size.asc()
        return ArtifactRevisionRow.size.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.created_at.asc()
        return ArtifactRevisionRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRevisionRow.updated_at.asc()
        return ArtifactRevisionRow.updated_at.desc()
