import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    LivenessStatus,
    ReadinessStatus,
)
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("DeploymentRouteRow",)


def _get_deployment_route_join_cond():
    from .model_deployment import ModelDeploymentRow

    return foreign(DeploymentRouteRow.deployment_id) == ModelDeploymentRow.id


def _get_session_join_cond():
    from .session import SessionRow

    return foreign(DeploymentRouteRow.session_id) == SessionRow.id


def _get_revision_join_cond():
    from .model_revision import ModelRevisionRow

    return foreign(DeploymentRouteRow.revision_id) == ModelRevisionRow.id


class DeploymentRouteRow(Base):
    __tablename__ = "deployment_routes"

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
    revision_id = sa.Column(
        "revision_id",
        GUID,
        nullable=False,
    )
    weight = sa.Column("weight", sa.Integer, nullable=False)
    readiness_status = sa.Column(
        "readiness_status",
        StrEnumType(ReadinessStatus),
        nullable=False,
    )
    liveness_status = sa.Column(
        "liveness_status",
        StrEnumType(LivenessStatus),
        nullable=False,
    )
    activeness_status = sa.Column(
        "activeness_status",
        StrEnumType(ActivenessStatus),
        nullable=False,
    )
    detail = sa.Column("detail", pgsql.JSONB, nullable=True)
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
        back_populates="deployment_route_rows",
        primaryjoin=_get_deployment_route_join_cond,
    )

    session_row = relationship(
        "SessionRow",
        primaryjoin=_get_session_join_cond,
    )

    revision_row = relationship(
        "ModelRevisionRow",
        primaryjoin=_get_revision_join_cond,
    )

    def __init__(
        self,
        deployment_id: uuid.UUID,
        session_id: uuid.UUID,
        revision_id: uuid.UUID,
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
            f"DeploymentRouteRow("
            f"id: {self.id}, "
            f"deployment_id: {self.deployment_id}, "
            f"session_id: {self.session_id}, "
            f"weight: {self.weight}, "
            f"readiness_status: {self.readiness_status.value}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
