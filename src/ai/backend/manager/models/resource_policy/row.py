from __future__ import annotations

from collections.abc import Sequence
from typing import Self

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ai.backend.common.types import DefaultForUnspecified
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.models.base import (
    Base,
    EnumType,
    ResourceSlotColumn,
    VFolderHostPermissionColumn,
    mapper_registry,
)

__all__: Sequence[str] = (
    "DefaultForUnspecified",
    "KeyPairResourcePolicyRow",
    "ProjectResourcePolicyRow",
    "UserResourcePolicyRow",
    "keypair_resource_policies",
    "project_resource_policies",
    "user_resource_policies",
)


keypair_resource_policies = sa.Table(
    "keypair_resource_policies",
    mapper_registry.metadata,
    sa.Column("name", sa.String(length=256), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "default_for_unspecified",
        EnumType(DefaultForUnspecified),
        default=DefaultForUnspecified.LIMITED,
        nullable=False,
    ),
    sa.Column("total_resource_slots", ResourceSlotColumn(), nullable=False),
    sa.Column("max_session_lifetime", sa.Integer(), nullable=False, server_default=sa.text("0")),
    sa.Column("max_concurrent_sessions", sa.Integer(), nullable=False),
    sa.Column("max_pending_session_count", sa.Integer(), nullable=True),
    sa.Column("max_pending_session_resource_slots", ResourceSlotColumn(), nullable=True),
    sa.Column(
        "max_concurrent_sftp_sessions", sa.Integer(), nullable=False, server_default=sa.text("1")
    ),
    sa.Column("max_containers_per_session", sa.Integer(), nullable=False),
    sa.Column("idle_timeout", sa.BigInteger(), nullable=False),
    sa.Column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default={},
    ),
    # TODO: implement with a many-to-many association table
    # sa.Column('allowed_scaling_groups', sa.Array(sa.String), nullable=False),
)


class KeyPairResourcePolicyRow(Base):
    __table__ = keypair_resource_policies
    keypairs = relationship("KeyPairRow", back_populates="resource_policy_row")

    def to_dataclass(
        self,
    ) -> KeyPairResourcePolicyData:
        return KeyPairResourcePolicyData(
            name=self.name,
            created_at=self.created_at,
            default_for_unspecified=self.default_for_unspecified,
            total_resource_slots=self.total_resource_slots,
            max_session_lifetime=self.max_session_lifetime,
            max_concurrent_sessions=self.max_concurrent_sessions,
            max_pending_session_count=self.max_pending_session_count,
            max_pending_session_resource_slots=self.max_pending_session_resource_slots,
            max_concurrent_sftp_sessions=self.max_concurrent_sftp_sessions,
            max_containers_per_session=self.max_containers_per_session,
            idle_timeout=self.idle_timeout,
            allowed_vfolder_hosts=self.allowed_vfolder_hosts,
        )


user_resource_policies = sa.Table(
    "user_resource_policies",
    mapper_registry.metadata,
    sa.Column("name", sa.String(length=256), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("max_vfolder_count", sa.Integer(), nullable=False),
    sa.Column("max_quota_scope_size", sa.BigInteger(), nullable=False),
    sa.Column("max_session_count_per_model_session", sa.Integer(), nullable=False),
    sa.Column("max_customized_image_count", sa.Integer(), nullable=False, default=3),
)


class UserResourcePolicyRow(Base):
    __table__ = user_resource_policies
    users = relationship("UserRow", back_populates="resource_policy_row")

    def __init__(
        self,
        name: str,
        max_vfolder_count: int,
        max_quota_scope_size: int,
        max_session_count_per_model_session: int,
        max_customized_image_count: int,
    ) -> None:
        self.name = name
        self.max_vfolder_count = max_vfolder_count
        self.max_quota_scope_size = max_quota_scope_size
        self.max_session_count_per_model_session = max_session_count_per_model_session
        self.max_customized_image_count = max_customized_image_count

    @classmethod
    def from_dataclass(cls, data: UserResourcePolicyData) -> Self:
        return cls(
            name=data.name,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_session_count_per_model_session=data.max_session_count_per_model_session,
            max_customized_image_count=data.max_customized_image_count,
        )

    def to_dataclass(self) -> UserResourcePolicyData:
        return UserResourcePolicyData(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_session_count_per_model_session=self.max_session_count_per_model_session,
            max_customized_image_count=self.max_customized_image_count,
        )


project_resource_policies = sa.Table(
    "project_resource_policies",
    mapper_registry.metadata,
    sa.Column("name", sa.String(length=256), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("max_vfolder_count", sa.Integer(), nullable=False),
    sa.Column("max_quota_scope_size", sa.BigInteger(), nullable=False),
    sa.Column("max_network_count", sa.Integer(), nullable=False),
)


class ProjectResourcePolicyRow(Base):
    __table__ = project_resource_policies
    projects = relationship("GroupRow", back_populates="resource_policy_row")

    def __init__(
        self,
        name: str,
        max_vfolder_count: int,
        max_quota_scope_size: int,
        max_network_count: int,
    ) -> None:
        self.name = name
        self.max_vfolder_count = max_vfolder_count
        self.max_quota_scope_size = max_quota_scope_size
        self.max_network_count = max_network_count

    @classmethod
    def from_dataclass(cls, data: ProjectResourcePolicyData) -> Self:
        return cls(
            name=data.name,
            max_vfolder_count=data.max_vfolder_count,
            max_quota_scope_size=data.max_quota_scope_size,
            max_network_count=data.max_network_count,
        )

    def to_dataclass(self) -> ProjectResourcePolicyData:
        return ProjectResourcePolicyData(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_network_count=self.max_network_count,
        )
