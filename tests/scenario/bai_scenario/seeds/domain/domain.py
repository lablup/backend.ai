"""Write specs for a domain."""

from __future__ import annotations

from bai_scenario.seeds.seeder import Spec

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.creators import DomainCreator


def seed_domain(*, name_hint: str = "domain", is_active: bool = True) -> Spec[DomainData]:
    """A domain. The name is the seeder's; the hint only says which row made it."""

    def build(name: str) -> DomainCreator:
        return DomainCreator(name=name, description=f"{name} was already here", is_active=is_active)

    return Spec(name_hint, build)
