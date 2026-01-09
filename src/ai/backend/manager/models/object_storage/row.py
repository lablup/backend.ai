from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.association_artifacts_storages import (
        AssociationArtifactsStorageRow,
    )
    from ai.backend.manager.models.storage_namespace import StorageNamespaceRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ObjectStorageRow",)


def _get_object_storage_association_artifact_join_cond():
    from ai.backend.manager.models.association_artifacts_storages import (
        AssociationArtifactsStorageRow,
    )

    return ObjectStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_namespace_id)


def _get_object_storage_namespace_join_cond():
    from ai.backend.manager.models.storage_namespace import StorageNamespaceRow

    return foreign(StorageNamespaceRow.storage_id) == ObjectStorageRow.id


class ObjectStorageRow(Base):
    """
    Represents an object storage configuration.
    This model is used to store the details of object storage services
    such as access keys, endpoints.
    """

    __tablename__ = "object_storages"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String, index=True, unique=True, nullable=False)
    host: Mapped[str] = mapped_column("host", sa.String, index=True, nullable=False)
    access_key: Mapped[str] = mapped_column(
        "access_key",
        sa.String,
        nullable=False,
    )
    secret_key: Mapped[str] = mapped_column(
        "secret_key",
        sa.String,
        nullable=False,
    )
    endpoint: Mapped[str] = mapped_column(
        "endpoint",
        sa.String,
        nullable=False,
    )
    region: Mapped[str | None] = mapped_column(
        "region",
        sa.String,
        nullable=True,
    )

    association_artifacts_storages_rows: Mapped[list[AssociationArtifactsStorageRow]] = (
        relationship(
            "AssociationArtifactsStorageRow",
            back_populates="object_storage_row",
            primaryjoin=_get_object_storage_association_artifact_join_cond,
            overlaps="vfs_storage_row",
        )
    )
    namespace_rows: Mapped[list[StorageNamespaceRow]] = relationship(
        "StorageNamespaceRow",
        back_populates="object_storage_row",
        primaryjoin=_get_object_storage_namespace_join_cond,
    )

    def __str__(self) -> str:
        return (
            f"ObjectStorageRow("
            f"id={self.id}, "
            f"name={self.name}, "
            f"host={self.host}, "
            f"access_key={self.access_key}, "
            f"secret_key={self.secret_key}, "
            f"endpoint={self.endpoint}, "
            f"region={self.region})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_dataclass(self) -> ObjectStorageData:
        return ObjectStorageData(
            id=self.id,
            name=self.name,
            host=self.host,
            access_key=self.access_key,
            secret_key=self.secret_key,
            endpoint=self.endpoint,
            region=self.region,
        )
