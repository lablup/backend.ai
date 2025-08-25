import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.model_deployment.types import ReadinessStatus
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    DecimalType,
    IDColumn,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("DeploymentNetworkBindingRow",)


def _get_deployment_network_binding_join_cond():
    from .model_deployment import ModelDeploymentRow

    return DeploymentNetworkBindingRow.deployment_id == foreign(ModelDeploymentRow.id)


def _get_session_join_cond():
    from .session import SessionRow

    return DeploymentNetworkBindingRow.session_id == foreign(SessionRow.id)


class DeploymentNetworkBindingRow(Base):
    __tablename__ = "deployment_network_bindings"

    id = IDColumn("id")

    deployment_id = sa.Column(
        "deployment_id",
        GUID,
        nullable=False,
    )
    session_id = sa.Column(
        "session_id",
        GUID,
        nullable=False,
    )
    weight = sa.Column("weight", DecimalType(), nullable=False)
    readiness_status = sa.Column(
        "readiness_status",
        StrEnumType(ReadinessStatus),
        nullable=False,
    )
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # Relationships
    model_deployment_row = relationship(
        "ModelDeploymentRow",
        back_populates="deployment_network_binding_rows",
        primaryjoin=_get_deployment_network_binding_join_cond,
    )

    session_row = relationship(
        "SessionRow",
        primaryjoin=_get_session_join_cond,
    )

    def __init__(
        self,
        deployment_id: uuid.UUID,
        session_id: uuid.UUID,
        weight: Decimal,
        readiness_status: ReadinessStatus,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.deployment_id = deployment_id
        self.session_id = session_id
        self.weight = weight
        self.readiness_status = readiness_status
        self.created_at = created_at
        self.updated_at = updated_at

    def __str__(self) -> str:
        return (
            f"DeploymentNetworkBindingRow("
            f"id: {self.id}, "
            f"deployment_id: {self.deployment_id}, "
            f"session_id: {self.session_id}, "
            f"weight: {self.weight}, "
            f"readiness_status: {self.readiness_status.value}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
