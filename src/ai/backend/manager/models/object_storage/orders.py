"""Query orders for the object_storage domain."""

from __future__ import annotations

from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base import QueryOrder


class ObjectStorageOrders:
    """QueryOrder factories for object storage sorting."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        col = ObjectStorageRow.name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def host(ascending: bool = True) -> QueryOrder:
        col = ObjectStorageRow.host
        return col.asc() if ascending else col.desc()

    @staticmethod
    def region(ascending: bool = True) -> QueryOrder:
        col = ObjectStorageRow.region
        return col.asc() if ascending else col.desc()
