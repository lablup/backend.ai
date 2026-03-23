"""Query orders for image rows."""

from __future__ import annotations

from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.repositories.base import QueryOrder

from .conditions import ImageConditions


class ImageOrders:
    """Query orders for images."""

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
        last_used_subq = ImageConditions._last_used_subquery()
        if ascending:
            return last_used_subq.asc()
        return last_used_subq.desc()


class ImageAliasOrders:
    """Query orders for image aliases."""

    @staticmethod
    def alias(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ImageAliasRow.alias.asc()
        return ImageAliasRow.alias.desc()
