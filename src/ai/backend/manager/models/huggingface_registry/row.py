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

__all__ = ("HuggingFaceRegistryRow",)


class HuggingFaceRegistryRow(RegistryNameMixin, Base):
    __tablename__ = "huggingface_registries"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    url: Mapped[str] = mapped_column("url", sa.String, nullable=False)
    token: Mapped[str | None] = mapped_column("token", sa.String, nullable=True, default=None)

    @override
    def __str__(self) -> str:
        return f"HuggingFaceRegistryRow(id={self.id}, url={self.url}, token={self.token})"

    @override
    def __repr__(self) -> str:
        return self.__str__()
