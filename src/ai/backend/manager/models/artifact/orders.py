"""Query orders for artifact repository."""

from __future__ import annotations

from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.repositories.base import QueryOrder


class ArtifactOrders:
    """Query orders for artifacts."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.name.asc()
        return ArtifactRow.name.desc()

    @staticmethod
    def type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.type.asc()
        return ArtifactRow.type.desc()

    @staticmethod
    def scanned_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.scanned_at.asc()
        return ArtifactRow.scanned_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ArtifactRow.updated_at.asc()
        return ArtifactRow.updated_at.desc()
