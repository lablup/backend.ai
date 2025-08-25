from __future__ import annotations

import logging

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.object_storage_meta.types import ObjectStorageMetaData
from ai.backend.manager.models.association_artifacts_storages import AssociationArtifactsStorageRow

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ObjectStorageRow",)


def _get_object_storage_association_artifact_join_cond():
    return ObjectStorageRow.id == foreign(AssociationArtifactsStorageRow.storage_id)


def _get_object_storage_meta_join_cond():
    return foreign(ObjectStorageMetaRow.storage_id) == ObjectStorageRow.id


class ObjectStorageMetaRow(Base):
    __tablename__ = "object_storage_meta"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("storage_id", "bucket", name="uq_storage_id_bucket"),
    )

    id = IDColumn("id")
    storage_id = sa.Column(
        "storage_id",
        GUID,
        nullable=False,
    )
    bucket = sa.Column("bucket", sa.String, nullable=False)

    object_storage_row = relationship(
        "ObjectStorageRow",
        back_populates="meta_rows",
        primaryjoin=_get_object_storage_meta_join_cond,
    )

    def to_dataclass(self) -> ObjectStorageMetaData:
        return ObjectStorageMetaData(
            id=self.id,
            storage_id=self.storage_id,
            bucket=self.bucket,
        )


class ObjectStorageRow(Base):
    """
    Represents an object storage configuration.
    This model is used to store the details of object storage services
    such as access keys, endpoints.
    """

    __tablename__ = "object_storages"

    id = IDColumn("id")
    name = sa.Column("name", sa.String, index=True, unique=True, nullable=False)
    host = sa.Column("host", sa.String, index=True, nullable=False)
    access_key = sa.Column(
        "access_key",
        sa.String,
        nullable=False,
    )
    secret_key = sa.Column(
        "secret_key",
        sa.String,
        nullable=False,
    )
    endpoint = sa.Column(
        "endpoint",
        sa.String,
        nullable=False,
    )
    region = sa.Column(
        "region",
        sa.String,
        nullable=True,
    )

    association_artifacts_storages_rows = relationship(
        "AssociationArtifactsStorageRow",
        back_populates="object_storage_row",
        primaryjoin=_get_object_storage_association_artifact_join_cond,
    )
    meta_rows = relationship(
        "ObjectStorageMetaRow",
        back_populates="object_storage_row",
        primaryjoin=_get_object_storage_meta_join_cond,
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
