from __future__ import annotations

import logging
import uuid
from typing import Sequence

import sqlalchemy as sa

from ai.backend.logging import BraceStyleAdapter

from .base import GUID, Base, IDColumn

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = ("AssociationContainerRegistriesGroupsRow",)


class AssociationContainerRegistriesGroupsRow(Base):
    __tablename__ = "association_container_registries_groups"
    id = IDColumn()
    registry_id = sa.Column(
        "registry_id",
        GUID,
        sa.ForeignKey("container_registries.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    group_id = sa.Column(
        "group_id",
        GUID,
        sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    def __init__(self, registry_id: uuid.UUID, group_id: uuid.UUID):
        self.registry_id = registry_id
        self.group_id = group_id
