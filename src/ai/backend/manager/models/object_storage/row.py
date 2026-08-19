from __future__ import annotations

import logging
import uuid
from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ObjectStorageRow",)


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

    @override
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

    @override
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
