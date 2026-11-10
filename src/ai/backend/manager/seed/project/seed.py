from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import cast, override

from pydantic import Field, field_validator

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_policy import ProjectResourcePolicyUUID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import ResourceSlot, VFolderHostPermission
from ai.backend.manager.models.base import SlugType
from ai.backend.manager.models.project.row import ProjectRow, ProjectType
from ai.backend.manager.models.project.upserters import ProjectUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class ProjectSeed(SeedItem):
    """One ``groups`` row. Its members and roles are not written by this kind."""

    id: ProjectID
    domain_id: DomainID
    name: str
    type: ProjectType = ProjectType.GENERAL
    resource_policy_id: ProjectResourcePolicyUUID
    creator_id: UserID | None = None
    description: str | None = Field(default=None, max_length=512)
    is_active: bool = True
    total_resource_slots: dict[str, Decimal] = {}
    allowed_vfolder_hosts: dict[str, list[VFolderHostPermission]] = {}

    @field_validator("name")
    @classmethod
    def _fits_the_column(cls, value: str) -> str:
        """The rule ``groups.name`` checks on bind, so the file fails ``seed check``."""
        cast(SlugType, ProjectRow.__table__.c.name.type).check(value)
        return value

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ProjectUpserter(
                id=self.id,
                domain_id=self.domain_id,
                project_type=self.type,
                creator_id=self.creator_id,
                name=self.name,
                resource_policy_id=self.resource_policy_id,
                description=self.description,
                is_active=self.is_active,
                total_resource_slots=ResourceSlot(self.total_resource_slots),
                allowed_vfolder_hosts=self.allowed_vfolder_hosts,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ProjectSeed]]) -> list[SeedRejection]:
        """None: the constraints on ``groups`` fail an item that repeats a name in its
        domain or a second personal project of one creator."""
        return []
