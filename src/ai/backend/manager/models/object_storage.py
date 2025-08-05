from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter

from .base import (
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
__all__ = ("ObjectStorageRow",)


class ObjectStorageRow(Base):
    """
    Represents an object storage configuration.
    This model is used to store the details of object storage services
    such as access keys, endpoints, and associated buckets.
    """
    __tablename__ = "object_storages"

    id = IDColumn("id")
    name = sa.Column("name", sa.String, index=True, unique=True, nullable=False)
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
    buckets = sa.Column(
        "buckets",
        sa.ARRAY(sa.String),
        nullable=True,
        index=True,
    )

    def __str__(self) -> str:
        return (
            f"ObjectStorageRow("
            f"id={self.id}, "
            f"access_key={self.access_key}, "
            f"secret_key={self.secret_key}, "
            f"endpoint={self.endpoint}, "
            f"region={self.region}, "
            f"buckets={self.buckets})"
        )

    def __repr__(self) -> str:
        return self.__str__()
