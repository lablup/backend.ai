from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("VFSStorageRow",)


class VFSStorageRow(Base):
    """
    Represents a VFS storage configuration.
    This model is used to store the details of VFS storage backends
    such as base paths, subpaths, and chunk sizes.
    """

    __tablename__ = "vfs_storages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String, index=True, unique=True, nullable=False)
    host: Mapped[str] = mapped_column("host", sa.String, nullable=False)
    base_path: Mapped[str] = mapped_column("base_path", sa.String, nullable=False)

    @override
    def __str__(self) -> str:
        return (
            f"VFSStorageRow("
            f"id={self.id}, "
            f"name={self.name}, "
            f"host={self.host}, "
            f"base_path={self.base_path})"
        )

    @override
    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> VFSStorageData:
        return VFSStorageData(
            id=self.id,
            name=self.name,
            host=self.host,
            base_path=Path(self.base_path),
        )
