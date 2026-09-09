"""What a domain scenario table says besides the call.

How the adapter is built lives in the tables' own conftest. This holds the words the
rows use: the rows they lay down, and the situations worth naming more than once.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from typing import Any, override

from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.testutils.typed_scenario import (
    Arrangement,
    Held,
    Situation,
    TypedScenario,
    config_of,
    recent,
    situation,
)
from bai_scenario.seeds.seeding import (
    DOMAIN_ADMIN_PRESET,
    Grown,
    SeedRoom,
    creates,
    holds,
    on_the_domain,
)

type DomainScenario = TypedScenario[DomainAdapter, ManagerUnifiedConfig]

MANAGER_CONFIG = config_of(ManagerUnifiedConfig)


def a_domain(named: str = "already-here") -> Grown[DomainData]:
    """A domain sitting in the database before the request arrives."""
    return creates(DomainCreator(name=named, description=description_of(named)))


def description_of(name: str) -> str | None:
    """What ``a_domain`` writes, so a table checking it cannot drift."""
    return f"{name} was already here"


def the_domain_admin_role() -> Held[SeedRoom]:
    """The domain's admin role. Holding it is what makes the refusals say something:
    the actor holds it and is still turned away, because that preset covers users
    rather than the domain entity."""
    return holds(DOMAIN_ADMIN_PRESET, on_the_domain())


def enforcement_off(setup: Arrangement[SeedRoom] | None = None) -> Situation[ManagerUnifiedConfig]:
    """The same set-up, in an install that does not enforce entity permissions."""
    return situation(
        setup=setup,
        config=[MANAGER_CONFIG.set(lambda c: c.manager.rbac.enforcement_enabled, False)],
    )


def within_the_run() -> Callable[[datetime], bool]:
    """A timestamp the run itself wrote."""
    return recent(timedelta(minutes=5))


# ---------------------------------------------------------------------------
# The set-ups a domain table shares. Each names what is in the database, and holds
# each row so a call reads it off the row rather than repeating a literal.
# ---------------------------------------------------------------------------


class ADomainIsThere(Arrangement[SeedRoom]):
    """One domain, already written when the request arrives.

    The values it was written with are held here too, so a row checking one reads it
    off the set-up rather than repeating a literal the seed also carries.
    """

    domain: Grown[DomainData]
    name: str
    description: str | None

    def __init__(self, named: str = "already-here") -> None:
        self.name = named
        self.description = description_of(named)
        self.domain = a_domain(named)

    @override
    def rows(self) -> Sequence[Grown[Any]]:
        return [self.domain]


class TheNameIsTaken(Arrangement[SeedRoom]):
    """A domain holding the name a creation is about to ask for."""

    domain: Grown[DomainData]
    name: str

    def __init__(self, name: str) -> None:
        self.name = name
        self.domain = a_domain(name)

    @override
    def rows(self) -> Sequence[Grown[Any]]:
        return [self.domain]


class TwoDomainsAreThere(Arrangement[SeedRoom]):
    """Two domains a filter has to tell apart."""

    first: Grown[DomainData]
    second: Grown[DomainData]
    first_name: str
    second_name: str

    def __init__(self, first: str, second: str) -> None:
        self.first_name = first
        self.second_name = second
        self.first = a_domain(first)
        self.second = a_domain(second)

    @override
    def rows(self) -> Sequence[Grown[Any]]:
        return [self.first, self.second]


class SomeDomainsAreThere(Arrangement[SeedRoom]):
    """A counted set of domains, so a table saying how many says it once."""

    domains: Sequence[Grown[DomainData]]
    count: int

    def __init__(self, count: int) -> None:
        self.count = count
        self.domains = [a_domain(f"already-{i}") for i in range(count)]

    @override
    def rows(self) -> Sequence[Grown[Any]]:
        return list(self.domains)
