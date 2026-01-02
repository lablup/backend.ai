"""CreatorSpec implementations for object storage domain."""

from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import override

from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class ObjectStorageCreatorSpec(CreatorSpec[ObjectStorageRow]):
    """CreatorSpec for object storage creation."""

    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str

    @override
    def build_row(self) -> ObjectStorageRow:
        return ObjectStorageRow(
            name=self.name,
            host=self.host,
            access_key=self.access_key,
            secret_key=self.secret_key,
            endpoint=self.endpoint,
            region=self.region,
        )
