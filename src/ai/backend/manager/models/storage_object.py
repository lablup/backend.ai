from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
__all__ = ("StorageObjectRow",)


class StorageObjectRow(Base):
    """
    Represents a storage object associated with an artifact.
    This model is used to track objects stored in the backend storage system,
    including their metadata such as size, checksum, and timestamps.
    """

    __tablename__ = "storage_objects"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("artifact_id", "object_key", name="uq_artifact_id_object_key"),
    )

    id = IDColumn("id")
    artifact_id = sa.Column(
        "artifact_id",
        sa.String,
        nullable=False,
        index=True,
    )
    object_key = sa.Column(
        "object_key",
        sa.String,
        nullable=False,
    )
    size_bytes = sa.Column(
        "size_bytes",
        sa.BigInteger,
        nullable=False,
    )
    checksum = sa.Column(
        "checksum",
        sa.String,
        nullable=True,
    )
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    def __str__(self) -> str:
        return (
            f"StorageObjectRow("
            f"id={self.id}, "
            f"artifact_id={self.artifact_id}, "
            f"object_key={self.object_key}, "
            f"size_bytes={self.size_bytes}, "
            f"checksum={self.checksum}, "
            f"created_at={self.created_at.isoformat()}, "
            f"updated_at={self.updated_at.isoformat()})"
        )

    def __repr__(self) -> str:
        return self.__str__()
