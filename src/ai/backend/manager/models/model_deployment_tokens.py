import logging
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    IDColumn,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__ = ("ModelDeploymentTokenRow",)


def _get_deployment_token_join_cond():
    from .model_deployment import ModelDeploymentRow

    return foreign(ModelDeploymentTokenRow.model_deployment_id) == ModelDeploymentRow.id


class ModelDeploymentTokenRow(Base):
    __tablename__ = "model_deployment_tokens"

    id = IDColumn("id")

    token = sa.Column("token", sa.String, nullable=False)
    model_deployment_id = sa.Column(
        "model_deployment_id",
        GUID,
        nullable=False,
    )
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True,
    )

    # Relationships
    model_deployment_row = relationship(
        "ModelDeploymentRow",
        back_populates="token_rows",
        primaryjoin=_get_deployment_token_join_cond,
    )

    def __init__(
        self,
        token: str,
        model_deployment_id: uuid.UUID,
        created_at: Optional[datetime] = None,
    ):
        self.token = token
        self.model_deployment_id = model_deployment_id
        self.created_at = created_at

    def __str__(self) -> str:
        return (
            f"ModelDeploymentTokenRow("
            f"id: {self.id}, "
            f"model_deployment_id: {self.model_deployment_id}, "
            f"created_at: {self.created_at}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
