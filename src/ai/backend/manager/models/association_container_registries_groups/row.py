from __future__ import annotations

import logging
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import GUID, Base, IDColumn

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = ("AssociationContainerRegistriesGroupsRow",)


def _get_container_registry_join_condition():
    from ai.backend.manager.models.container_registry import ContainerRegistryRow

    return ContainerRegistryRow.id == foreign(AssociationContainerRegistriesGroupsRow.registry_id)


def _get_group_join_condition():
    from ai.backend.manager.models.group import GroupRow

    return GroupRow.id == foreign(AssociationContainerRegistriesGroupsRow.group_id)


class AssociationContainerRegistriesGroupsRow(Base):
    __tablename__ = "association_container_registries_groups"
    __table_args__ = (
        # constraint
        sa.UniqueConstraint("registry_id", "group_id", name="uq_registry_id_group_id"),
    )

    id = IDColumn()
    registry_id = sa.Column(
        "registry_id",
        GUID,
        nullable=False,
    )
    group_id = sa.Column(
        "group_id",
        GUID,
        nullable=False,
    )

    container_registry_row = relationship(
        "ContainerRegistryRow",
        back_populates="association_container_registries_groups_rows",
        primaryjoin=_get_container_registry_join_condition,
    )

    group_row = relationship(
        "GroupRow",
        back_populates="association_container_registries_groups_rows",
        primaryjoin=_get_group_join_condition,
    )
