"""DataUpdater implementations for the object storage repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ObjectStorageUpdater(DataUpdater[ObjectStorageRow, ObjectStorageData]):
    storage_id: uuid.UUID
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    host: OptionalState[str] = field(default_factory=OptionalState.nop)
    access_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    secret_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    endpoint: OptionalState[str] = field(default_factory=OptionalState.nop)
    region: TriState[str] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[ObjectStorageRow]:
        return ObjectStorageRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.storage_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.host.update_dict(to_update, "host")
        self.access_key.update_dict(to_update, "access_key")
        self.secret_key.update_dict(to_update, "secret_key")
        self.endpoint.update_dict(to_update, "endpoint")
        self.region.update_dict(to_update, "region")
        return to_update

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return row.to_dataclass()
