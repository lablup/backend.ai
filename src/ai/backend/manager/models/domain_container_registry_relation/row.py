from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.models.base import GUID, Base

__all__: Sequence[str] = ("DomainContainerRegistryRelationRow",)


class DomainContainerRegistryRelationRow(Base):
    """A container registry a domain is allowed on. Removing either end deletes the row."""

    __tablename__ = "domain_container_registry_relations"

    domain_id: Mapped[DomainID] = mapped_column(
        "domain_id",
        GUID(DomainID),
        sa.ForeignKey("domains.id", ondelete="CASCADE"),
        primary_key=True,
    )
    container_registry_id: Mapped[ContainerRegistryID] = mapped_column(
        "container_registry_id",
        GUID(ContainerRegistryID),
        sa.ForeignKey(
            "container_registries.id",
            name="fk_domain_container_registry_relations_container_registry_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        index=True,
    )
