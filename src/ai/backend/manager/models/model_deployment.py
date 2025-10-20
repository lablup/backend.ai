import logging
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import foreign, relationship

from ai.backend.common.data.model_deployment.types import DeploymentStrategy, ModelDeploymentStatus
from ai.backend.logging import BraceStyleAdapter

from .base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__ = ("ModelDeploymentRow",)


def _get_deployment_revision_join_cond():
    from .model_revision import ModelRevisionRow

    return ModelDeploymentRow.id == foreign(ModelRevisionRow.model_deployment_id)


def _get_deployment_token_join_cond():
    from .model_deployment_tokens import ModelDeploymentTokenRow

    return ModelDeploymentRow.id == foreign(ModelDeploymentTokenRow.model_deployment_id)


def _get_deployment_auto_scaling_rule_join_cond():
    from .model_deployment_auto_scaling_rules import ModelDeploymentAutoScalingRuleRow

    return ModelDeploymentRow.id == foreign(ModelDeploymentAutoScalingRuleRow.model_deployment_id)


def _get_deployment_route_join_cond():
    from .deployment_route import DeploymentRouteRow

    return ModelDeploymentRow.id == foreign(DeploymentRouteRow.deployment_id)


def _get_deployment_user_join_cond():
    from .user import UserRow

    return UserRow.uuid == foreign(ModelDeploymentRow.created_user_id)


def _get_deployment_state_join_cond():
    from .deployment_state import DeploymentStateRow

    return ModelDeploymentRow.id == foreign(DeploymentStateRow.deployment_id)


class ModelDeploymentRow(Base):
    __tablename__ = "model_deployments"

    id = IDColumn("id")

    name = sa.Column("name", sa.String, index=True, nullable=False)
    status = sa.Column(
        "status",
        StrEnumType(ModelDeploymentStatus),
        nullable=False,
    )
    tags = sa.Column("tags", sa.String, nullable=False, default="")

    endpoint_url = sa.Column("endpoint_url", sa.String, nullable=True)
    preferred_domain_name = sa.Column("preferred_domain_name", sa.String, nullable=True)
    open_to_public = sa.Column("open_to_public", sa.Boolean, nullable=False)

    desired_replica_count = sa.Column("desired_replica_count", sa.Integer, nullable=False)
    created_user_id = sa.Column(
        "created_user_id",
        GUID,
        index=True,
        nullable=False,
    )
    current_revision_id = sa.Column("current_revision_id", GUID, nullable=False)

    default_deployment_strategy_type = sa.Column(
        "default_deployment_strategy_type",
        StrEnumType(DeploymentStrategy),
        nullable=False,
    )
    deployment_state_id = sa.Column(
        "deployment_state_id",
        GUID,
        nullable=True,
    )

    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=True,
    )
    updated_at = sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=True,
    )

    # Relationships
    revision_rows = relationship(
        "ModelRevisionRow",
        back_populates="model_deployment_row",
        primaryjoin=_get_deployment_revision_join_cond,
    )
    token_rows = relationship(
        "ModelDeploymentTokenRow",
        back_populates="model_deployment_row",
        primaryjoin=_get_deployment_token_join_cond,
    )
    auto_scaling_rule_rows = relationship(
        "ModelDeploymentAutoScalingRuleRow",
        back_populates="model_deployment_row",
        primaryjoin=_get_deployment_auto_scaling_rule_join_cond,
    )
    deployment_route_rows = relationship(
        "DeploymentRouteRow",
        back_populates="model_deployment_row",
        primaryjoin=_get_deployment_route_join_cond,
    )
    created_user_row = relationship(
        "UserRow",
        primaryjoin=_get_deployment_user_join_cond,
    )
    deployment_state_rows = relationship(
        "DeploymentStateRow",
        primaryjoin=_get_deployment_state_join_cond,
    )

    def __init__(
        self,
        name: str,
        status: ModelDeploymentStatus,
        tags: str,
        open_to_public: bool,
        desired_replica_count: int,
        created_user: uuid.UUID,
        current_revision_id: uuid.UUID,
        deployment_strategy_type: DeploymentStrategy,
        deployment_strategy_id: uuid.UUID,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        endpoint_url: Optional[str] = None,
        preferred_domain_name: Optional[str] = None,
    ):
        self.name = name
        self.status = status
        self.tags = tags
        self.created_at = created_at
        self.updated_at = updated_at
        self.endpoint_url = endpoint_url
        self.preferred_domain_name = preferred_domain_name
        self.open_to_public = open_to_public
        self.desired_replica_count = desired_replica_count
        self.created_user = created_user
        self.current_revision_id = current_revision_id
        self.deployment_strategy_type = deployment_strategy_type
        self.deployment_strategy_id = deployment_strategy_id

    def __str__(self) -> str:
        return (
            f"ModelDeploymentRow("
            f"id: {self.id}, "
            f"name: {self.name}, "
            f"status: {self.status.value}, "
            f"created_user: {self.created_user}, "
            f"current_revision_id: {self.current_revision_id}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__()
