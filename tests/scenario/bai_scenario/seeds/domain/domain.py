"""Write specs for a domain."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.types import VFolderHostPermission
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.creators import DomainCreator
from bai_scenario.seeds.seeder import Naming, SeedRow


@dataclass(frozen=True)
class SeedDomain(SeedRow[DomainData]):
    """A domain. The name is the seeder's; the hint only says which row made it.

    ``vfolder_hosts`` are the storage hosts folders of this domain may land on. A
    scenario that makes a folder has to name one the fake storage answers for.
    """

    name_hint: str = "domain"
    description: str = "심어둔 도메인"
    is_active: bool = True
    vfolder_hosts: Sequence[str] = field(default_factory=tuple)

    @override
    def kind(self) -> str:
        return "도메인"

    @override
    def detail(self) -> str:
        allows = [] if self.is_active else ["폐기된 상태"]
        if self.vfolder_hosts:
            allows.append(f"이 도메인의 폴더는 {', '.join(self.vfolder_hosts)}에 놓을 수 있다")
        return ", ".join(allows)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> DomainCreator:
        return DomainCreator(
            name=name,
            description=self.description,
            is_active=self.is_active,
            allowed_vfolder_hosts={
                host: [p.value for p in VFolderHostPermission] for host in self.vfolder_hosts
            },
        )
