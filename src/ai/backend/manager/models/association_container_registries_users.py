import logging
import uuid
from typing import Sequence

import sqlalchemy as sa

from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.manager.models.base import GUID, Base, IDColumn

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = ("AssociationContainerRegistriesUsers",)


class AssociationContainerRegistriesUsers(Base):
    __tablename__ = "association_container_registries_users"
    id = IDColumn()
    container_registry_id = sa.Column(
        "container_registry_id",
        GUID,
        sa.ForeignKey("container_registries.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = sa.Column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    def __init__(self, container_registry_id: uuid.UUID, user_id: uuid.UUID):
        self.container_registry_id = container_registry_id
        self.user_id = user_id
