"""Query orders for runtime variant preset rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow

__all__ = ("RuntimeVariantPresetOrders",)


class RuntimeVariantPresetOrders:
    @staticmethod
    def rank(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.rank.asc()
        return RuntimeVariantPresetRow.rank.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.name.asc()
        return RuntimeVariantPresetRow.name.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.id.asc()
        return RuntimeVariantPresetRow.id.desc()

    @staticmethod
    def added_version(ascending: bool = True) -> list[QueryOrder]:
        """A NULL lower bound is unbounded, so it sorts first."""
        columns = (
            RuntimeVariantPresetRow.added_version_major,
            RuntimeVariantPresetRow.added_version_minor,
            RuntimeVariantPresetRow.added_version_patch,
        )
        if ascending:
            return [column.asc().nullsfirst() for column in columns]
        return [column.desc().nullslast() for column in columns]

    @staticmethod
    def deprecated_version(ascending: bool = True) -> list[QueryOrder]:
        """A NULL upper bound is unbounded, so it sorts last."""
        columns = (
            RuntimeVariantPresetRow.deprecated_version_major,
            RuntimeVariantPresetRow.deprecated_version_minor,
            RuntimeVariantPresetRow.deprecated_version_patch,
        )
        if ascending:
            return [column.asc().nullslast() for column in columns]
        return [column.desc().nullsfirst() for column in columns]

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RuntimeVariantPresetRow.created_at.asc()
        return RuntimeVariantPresetRow.created_at.desc()
