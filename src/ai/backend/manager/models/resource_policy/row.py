from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermissionMap,
)
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
)

if TYPE_CHECKING:
    from ai.backend.manager.models.group import GroupRow
    from ai.backend.manager.models.keypair import KeyPairRow
    from ai.backend.manager.models.user import UserRow

__all__: Sequence[str] = (
    "DefaultForUnspecified",
    "KeyPairResourcePolicyRow",
    "ProjectResourcePolicyRow",
    "UserResourcePolicyRow",
    "keypair_resource_policies",
    "project_resource_policies",
    "user_resource_policies",
)


class KeyPairResourcePolicyRow(Base):  # type: ignore[misc]
    __tablename__ = "keypair_resource_policies"

    name: Mapped[str] = mapped_column("name", sa.String(length=256), primary_key=True)
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    default_for_unspecified: Mapped[DefaultForUnspecified] = mapped_column(
        "default_for_unspecified",
        EnumType(DefaultForUnspecified),
        default=DefaultForUnspecified.LIMITED,
        nullable=False,
    )
    total_resource_slots: Mapped[ResourceSlot] = mapped_column(
        "total_resource_slots", ResourceSlotColumn(), nullable=False
    )
    max_session_lifetime: Mapped[int] = mapped_column(
        "max_session_lifetime", sa.Integer(), nullable=False, server_default=sa.text("0")
    )
    max_concurrent_sessions: Mapped[int] = mapped_column(
        "max_concurrent_sessions", sa.Integer(), nullable=False
    )
    max_pending_session_count: Mapped[int | None] = mapped_column(
        "max_pending_session_count", sa.Integer(), nullable=True
    )
    max_pending_session_resource_slots: Mapped[ResourceSlot | None] = mapped_column(
        "max_pending_session_resource_slots", ResourceSlotColumn(), nullable=True
    )
    max_concurrent_sftp_sessions: Mapped[int] = mapped_column(
        "max_concurrent_sftp_sessions", sa.Integer(), nullable=False, server_default=sa.text("1")
    )
    max_containers_per_session: Mapped[int] = mapped_column(
        "max_containers_per_session", sa.Integer(), nullable=False
    )
    idle_timeout: Mapped[int] = mapped_column("idle_timeout", sa.BigInteger(), nullable=False)
    allowed_vfolder_hosts: Mapped[VFolderHostPermissionMap] = mapped_column(
        "allowed_vfolder_hosts",
        VFolderHostPermissionColumn(),
        nullable=False,
        default={},
    )
    # TODO: implement with a many-to-many association table
    # allowed_scaling_groups: Mapped[list[str]] = mapped_column(sa.Array(sa.String), nullable=False)

    keypairs: Mapped[list[KeyPairRow]] = relationship(
        "KeyPairRow", back_populates="resource_policy_row"
    )

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


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use KeyPairResourcePolicyRow class directly for new code.
keypair_resource_policies = KeyPairResourcePolicyRow.__table__


class UserResourcePolicyRow(Base):  # type: ignore[misc]
    __tablename__ = "user_resource_policies"

    name: Mapped[str] = mapped_column("name", sa.String(length=256), primary_key=True)
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    max_vfolder_count: Mapped[int] = mapped_column(
        "max_vfolder_count", sa.Integer(), nullable=False
    )
    max_quota_scope_size: Mapped[int] = mapped_column(
        "max_quota_scope_size", sa.BigInteger(), nullable=False
    )
    max_session_count_per_model_session: Mapped[int] = mapped_column(
        "max_session_count_per_model_session", sa.Integer(), nullable=False
    )
    max_customized_image_count: Mapped[int] = mapped_column(
        "max_customized_image_count", sa.Integer(), nullable=False, default=3
    )

    users: Mapped[list[UserRow]] = relationship("UserRow", back_populates="resource_policy_row")

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


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use UserResourcePolicyRow class directly for new code.
user_resource_policies = UserResourcePolicyRow.__table__


class ProjectResourcePolicyRow(Base):  # type: ignore[misc]
    __tablename__ = "project_resource_policies"

    name: Mapped[str] = mapped_column("name", sa.String(length=256), primary_key=True)
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    max_vfolder_count: Mapped[int] = mapped_column(
        "max_vfolder_count", sa.Integer(), nullable=False
    )
    max_quota_scope_size: Mapped[int] = mapped_column(
        "max_quota_scope_size", sa.BigInteger(), nullable=False
    )
    max_network_count: Mapped[int] = mapped_column(
        "max_network_count", sa.Integer(), nullable=False
    )

    projects: Mapped[list[GroupRow]] = relationship(
        "GroupRow", back_populates="resource_policy_row"
    )

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


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use ProjectResourcePolicyRow class directly for new code.
project_resource_policies = ProjectResourcePolicyRow.__table__
