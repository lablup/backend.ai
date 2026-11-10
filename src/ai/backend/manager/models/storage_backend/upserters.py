from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.entity.storage_backend_type import StorageBackendTypeID
from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendType,
)
from ai.backend.manager.data.storage_backend.types import StorageBackendTypeData
from ai.backend.manager.models.specs.created_in import CreatedInGlobal, CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.storage_backend.row import StorageBackendRow, StorageBackendTypeRow

__all__ = (
    "StorageBackendTypeUpserter",
    "StorageBackendUpserter",
)


@dataclass
class StorageBackendTypeUpserter(
    CreatedInPublic[StorageBackendTypeRow],
    EntityUpserter[StorageBackendTypeRow, StorageBackendTypeData],
):
    """Upserter for one storage backend implementation.

    Conflict key: ``name``. An update replaces ``capabilities``.
    """

    name: StorageBackendType
    capabilities: StorageBackendCapabilities

    @override
    def entity_id(self, row: StorageBackendTypeRow) -> StorageBackendTypeID:
        return StorageBackendTypeID(row.id)

    @override
    def row_class(self) -> type[StorageBackendTypeRow]:
        return StorageBackendTypeRow

    @override
    def index_elements(self) -> list[str]:
        return ["name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self.name, "capabilities": self.capabilities}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {"capabilities": self.capabilities, "updated_at": sa.func.now()}

    @override
    def to_data(self, row: StorageBackendTypeRow) -> StorageBackendTypeData:
        return row.to_data()


@dataclass
class StorageBackendUpserter(
    CreatedInGlobal[StorageBackendRow], EntityUpserter[StorageBackendRow, StorageBackendID]
):
    """Upsert spec for one storage backend.

    Conflict key: ``name``. A backend already there is left as it stands.
    """

    name: str
    storage_backend_type_id: StorageBackendTypeID

    @override
    def entity_id(self, row: StorageBackendRow) -> StorageBackendID:
        return StorageBackendID(row.id)

    @override
    def row_class(self) -> type[StorageBackendRow]:
        return StorageBackendRow

    @override
    def index_elements(self) -> list[str]:
        return ["name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self.name, "storage_backend_type_id": self.storage_backend_type_id}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {}

    @override
    def to_data(self, row: StorageBackendRow) -> StorageBackendID:
        return StorageBackendID(row.id)
