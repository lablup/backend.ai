from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRoleGrantWrite
from ai.backend.manager.seed.base import SeedItems, SeedRejection, SeedRelationItem


class DomainAdminSeed(SeedRelationItem):
    """One user granted the ``domain_admin`` role of a domain. The role is the one
    ``mgr permissions provision`` created from the role preset; this item writes only
    the grant."""

    preset_name: ClassVar[str] = "domain_admin"

    domain_id: DomainID
    user_id: UserID

    @override
    def key(self) -> str:
        return f"{self.domain_id}:{self.user_id}"

    @override
    def write(self) -> SeedRoleGrantWrite:
        return SeedRoleGrantWrite(
            user_id=self.user_id,
            scope=self.domain_id,
            preset_name=self.preset_name,
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[DomainAdminSeed]]) -> list[SeedRejection]:
        """None: an item naming a domain whose role is not provisioned, or a missing
        user, fails when it is written."""
        return []
