from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import GUID, Base

if TYPE_CHECKING:
    from ai.backend.manager.models.container_registry import ContainerRegistryRow
    from ai.backend.manager.models.group import GroupRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = ("AssociationContainerRegistriesGroupsRow",)


def _get_container_registry_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.container_registry import ContainerRegistryRow

    return ContainerRegistryRow.id == foreign(AssociationContainerRegistriesGroupsRow.registry_id)


def _get_group_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.group import GroupRow

    return GroupRow.id == foreign(AssociationContainerRegistriesGroupsRow.group_id)


class AssociationContainerRegistriesGroupsRow(Base):
    __tablename__ = "association_container_registries_groups"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("registry_id", "group_id", name="uq_registry_id_group_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    registry_id: Mapped[uuid.UUID] = mapped_column(
        "registry_id",
        GUID,
        nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        "group_id",
        GUID,
        nullable=False,
    )

    container_registry_row: Mapped[ContainerRegistryRow] = relationship(
        "ContainerRegistryRow",
        back_populates="association_container_registries_groups_rows",
        primaryjoin=_get_container_registry_join_condition,
    )

    group_row: Mapped[GroupRow] = relationship(
        "GroupRow",
        back_populates="association_container_registries_groups_rows",
        primaryjoin=_get_group_join_condition,
    )
