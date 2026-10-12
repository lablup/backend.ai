from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.storage_backend_type import StorageBackendTypeID
from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendType,
)
from ai.backend.manager.data.storage_backend.types import StorageBackendTypeData
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.storage_backend.row import StorageBackendTypeRow

__all__ = ("StorageBackendTypeUpserter",)


@dataclass
class StorageBackendTypeUpserter(
    CreatedInGlobal[StorageBackendTypeRow],
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
