"""Query orders for image rows."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.image import ImageAliasRow, ImageRow


class ImageOrders:
    """Query orders for images."""

    @staticmethod
    def canonical_match_first(canonical: str, architecture: str) -> QueryOrder:
        matches = sa.and_(ImageRow.name == canonical, ImageRow.architecture == architecture)
        return sa.case((matches, 0), else_=1).asc()

    @staticmethod
    def alive_first() -> QueryOrder:
        return sa.case((ImageRow.status == ImageStatus.ALIVE, 0), else_=1).asc()

    @staticmethod
    def alive_then_oldest() -> list[QueryOrder]:
        return [ImageOrders.alive_first(), ImageOrders.created_at()]

    @staticmethod
    def canonical_match_then_alive_then_oldest(
        canonical: str, architecture: str
    ) -> list[QueryOrder]:
        return [
            ImageOrders.canonical_match_first(canonical, architecture),
            *ImageOrders.alive_then_oldest(),
        ]

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.name.asc()
        return ImageRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.created_at.asc()
        return ImageRow.created_at.desc()

    @staticmethod
    def architecture(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.architecture.asc()
        return ImageRow.architecture.desc()

    @staticmethod
    def size_bytes(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.size_bytes.asc()
        return ImageRow.size_bytes.desc()

    @staticmethod
    def registry(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.registry.asc()
        return ImageRow.registry.desc()

    @staticmethod
    def tag(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.tag.asc()
        return ImageRow.tag.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.status.asc()
        return ImageRow.status.desc()

    @staticmethod
    def last_used(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageRow.last_used_at.asc()
        return ImageRow.last_used_at.desc()


class ImageAliasOrders:
    """Query orders for image aliases."""

    @staticmethod
    def alias(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageAliasRow.alias.asc()
        return ImageAliasRow.alias.desc()
