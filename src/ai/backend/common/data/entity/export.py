"""Entity type of the export reports."""

from typing import override

from ai.backend.common.data.entity.types import EntityType

__all__ = ("ExportEntityType",)


class ExportEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "export"

    @override
    @classmethod
    def description(cls) -> str:
        return "A data export operation, which names no row."
