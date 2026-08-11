from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ObjectStorageCreator(GlobalEntityCreator[ObjectStorageRow, ObjectStorageData]):
    """Creator for an object storage registration."""

    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

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

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return row.to_dataclass()
