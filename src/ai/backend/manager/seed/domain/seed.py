from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import cast, override

from pydantic import field_validator

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import ResourceSlot, VFolderHostPermission
from ai.backend.manager.models.base import SlugType
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.upserters import DomainUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class DomainSeed(SeedItem):
    """One ``domains`` row. Its roles, members and model-store project are items of
    their own kinds."""

    id: DomainID
    name: str
    description: str | None = None
    is_active: bool = True
    is_default: bool = False
    total_resource_slots: dict[str, Decimal] = {}
    allowed_vfolder_hosts: dict[str, list[VFolderHostPermission]] = {}
    allowed_docker_registries: list[str] = []

    @field_validator("name")
    @classmethod
    def _fits_the_column(cls, value: str) -> str:
        """The rule ``domains.name`` checks on bind, so the file fails ``seed check``."""
        cast(SlugType, DomainRow.__table__.c.name.type).check(value)
        return value

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=DomainUpserter(
                id=self.id,
                name=self.name,
                description=self.description,
                is_active=self.is_active,
                is_default=self.is_default,
                total_resource_slots=ResourceSlot(self.total_resource_slots),
                allowed_vfolder_hosts=self.allowed_vfolder_hosts,
                allowed_docker_registries=self.allowed_docker_registries,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[DomainSeed]]) -> list[SeedRejection]:
        """None: the constraints on ``domains`` fail an item that repeats a name or a
        second default."""
        return []
