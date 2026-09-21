from __future__ import annotations

import logging
import uuid
from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import (
    GUID,
    Base,
)
from ai.backend.manager.models.mixins.registry_name import RegistryNameMixin

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("ReservoirRegistryRow",)


class ReservoirRegistryRow(RegistryNameMixin, Base):
    __tablename__ = "reservoir_registries"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    endpoint: Mapped[str] = mapped_column("endpoint", sa.String, nullable=False)
    access_key: Mapped[str] = mapped_column("access_key", sa.String, nullable=False)
    secret_key: Mapped[str] = mapped_column("secret_key", sa.String, nullable=False)
    api_version: Mapped[str] = mapped_column("api_version", sa.String, nullable=False)

    @override
    def __str__(self) -> str:
        return f"ReservoirRegistryRow(id={self.id}, endpoint={self.endpoint}, api_version={self.api_version})"

    @override
    def __repr__(self) -> str:
        return self.__str__()
