"""CreatorSpec implementations for storage namespace domain."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from typing_extensions import override

from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class StorageNamespaceCreatorSpec(CreatorSpec[StorageNamespaceRow]):
    """CreatorSpec for storage namespace registration."""

    storage_id: uuid.UUID
    bucket: str

    @override
    def build_row(self) -> StorageNamespaceRow:
        return StorageNamespaceRow(
            storage_id=self.storage_id,
            namespace=self.bucket,
        )
