import logging

import sqlalchemy as sa

from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("DeploymentStateRow",)


class DeploymentStateRow(Base):
    __tablename__ = "deployment_states"

    id = IDColumn("id")

    deployment_id = sa.Column("deployment_id", GUID(), nullable=False)
    prev_revision_id = sa.Column("prev_revision_id", GUID(), nullable=False)
    next_revision_id = sa.Column("next_revision_id", GUID(), nullable=True)
    strategy = sa.Column("strategy", StrEnumType(DeploymentStrategy), nullable=False)
    status = sa.Column("status", StrEnumType(ModelDeploymentStatus), nullable=False)

    created_at = sa.Column("created_at", sa.DateTime, default=sa.func.now(), nullable=False)
    updated_at = sa.Column(
        "updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )

    def __init__(
        self,
        deployment_id: str,
        prev_revision_id: str,
        next_revision_id: str,
        strategy: DeploymentStrategy,
        status: str,
        created_at: str,
        updated_at: str,
    ):
        self.deployment_id = deployment_id
        self.prev_revision_id = prev_revision_id
        self.next_revision_id = next_revision_id
        self.strategy = strategy
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def __str__(self) -> str:
        return (
            f"DeploymentStateRow("
            f"id: {self.id}, "
            f"deployment_id: {self.deployment_id}, "
            f"prev_revision_id: {self.prev_revision_id}, "
            f"next_revision_id: {self.next_revision_id}, "
            f"strategy: {self.strategy}, "
            f"status: {self.status}, "
            f"created_at: {self.created_at}, "
            f"updated_at: {self.updated_at}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
