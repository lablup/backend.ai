"""Write specs for a domain."""

from __future__ import annotations

from collections.abc import Sequence

from bai_scenario.seeds.seeder import Spec

from ai.backend.common.types import VFolderHostPermission
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.creators import DomainCreator


def seed_domain(
    *,
    name_hint: str = "domain",
    is_active: bool = True,
    vfolder_hosts: Sequence[str] = (),
) -> Spec[DomainData]:
    """A domain. The name is the seeder's; the hint only says which row made it.

    ``vfolder_hosts`` are the storage hosts folders of this domain may land on. A
    scenario that makes a folder has to name one the fake storage answers for.
    """

    def build(name: str) -> DomainCreator:
        return DomainCreator(
            name=name,
            description=f"{name} was already here",
            is_active=is_active,
            allowed_vfolder_hosts={
                host: [p.value for p in VFolderHostPermission] for host in vfolder_hosts
            },
        )

    return Spec("a domain", name_hint, build)
