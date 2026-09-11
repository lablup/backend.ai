"""What an app config scenario table says besides the call.

The four app config adapters share one design: a definition registers a name, an
allow-list entry opens it to one scope kind, and a fragment holds a value under that.
What every table needs is here — the design laid as one nest, and the users a row calls
as. The merged read's own situations are here too; the other three adapters keep theirs
beside their tables. How an adapter is built lives in each table's own conftest.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override

from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.seeds.app_config.allow_list import SCOPE_NAMES, SeedAllowListEntry
from bai_scenario.seeds.app_config.definition import SeedDefinition
from bai_scenario.seeds.app_config.fragment import SeedFragmentOf, SeedPublicFragment
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config import AppConfigEntityType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListEntityType
from ai.backend.common.data.entity.app_config_definition import AppConfigDefinitionEntityType
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.app_config.response import GetAppConfigsPayload
from ai.backend.manager.data.app_config.types import (
    AppConfigAllowListData,
    AppConfigDefinitionData,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)

ENFORCEMENT = "manager.rbac.enforcement_enabled"

UNREGISTERED = "unregistered"
"""아무 정의도 갖지 않은 이름. 심은 것이 아니므로 리터럴로 둔다."""

ENTITY_NAMES: Mapping[EntityType, str] = {
    AppConfigEntityType(): "설정",
    AppConfigDefinitionEntityType(): "설정 정의",
    AppConfigAllowListEntityType(): "허용 항목",
    AppConfigFragmentEntityType(): "조각",
}
"""권한이 걸리는 엔티티 종류를 레포트가 부르는 말."""


def names_of(granted: Sequence[Permission]) -> str:
    return ", ".join(one.name or str(int(one)) for one in granted)


@dataclass(frozen=True)
class SomeoneGrantedOnTheirOwn(SeedNest[Laid[UserData]]):
    """자기 스코프에 앉은 역할로, 한 엔티티 종류에 정해진 권한만 받은 사용자.

    권한을 하나도 대지 않으면 역할을 만들지 않는다.
    """

    domain: Laid[DomainData]
    entity_type: EntityType
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        what = ENTITY_NAMES[self.entity_type]
        if not self.granted:
            return f"{what} 권한을 하나도 받지 않은 사용자 준비"
        return f"자기 스코프에서 {what}에 {names_of(self.granted)} 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        if not self.granted:
            return someone
        role = seed.creating_from(SeedRole(lambda u: UserID(u.id), name_hint="own-scope"), someone)
        for one in self.granted:
            seed.adding(SeedPermission(entity_type=self.entity_type, permission=one), role)
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class SomeoneGrantedOn[Seat](SeedNest[Laid[UserData]]):
    """주어진 스코프 행에 앉은 역할로, 한 엔티티 종류에 정해진 권한만 받은 사용자.

    도메인에 앉히면 그 도메인 안의 것을 다스린다.
    """

    domain: Laid[DomainData]
    seat: Laid[Seat]
    seat_id: Callable[[Seat], EntityIdentifier]
    entity_type: EntityType
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        what = ENTITY_NAMES[self.entity_type]
        if not self.granted:
            return f"{what} 권한을 하나도 받지 않은 사용자 준비"
        return f"{self.seat.describe}에서 {what}에 {names_of(self.granted)} 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        if not self.granted:
            return someone
        role = seed.creating_from(SeedRole(self.seat_id, name_hint="seated"), self.seat)
        for one in self.granted:
            seed.adding(SeedPermission(entity_type=self.entity_type, permission=one), role)
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class LaidDesign:
    """정의 하나와, 그 이름을 여는 허용 항목들의 손잡이."""

    definition: Laid[AppConfigDefinitionData]
    entries: Mapping[AppConfigScopeType, Laid[AppConfigAllowListData]]


@dataclass(frozen=True)
class ADesignOf(SeedNest[LaidDesign]):
    """이름 하나를 등록하고, 대준 스코프 종류마다 허용 항목을 연다.

    ``ranks``에 없는 종류는 그 종류의 기본 순위를 받는다.
    """

    allowed: tuple[AppConfigScopeType, ...] = ()
    ranks: Mapping[AppConfigScopeType, int] = field(default_factory=dict)
    name_hint: str = "config"

    @override
    def kind(self) -> str:
        if not self.allowed:
            return "아무 스코프에도 열리지 않은 이름 준비"
        opened = "·".join(SCOPE_NAMES[one] for one in self.allowed)
        return f"{opened} 스코프에 열린 이름 준비"

    @override
    def lay(self, seed: Seeder) -> LaidDesign:
        definition = seed.creating(SeedDefinition(name_hint=self.name_hint))
        entries = {
            one: seed.creating_from(
                SeedAllowListEntry(scope_type=one, rank=self.ranks.get(one)), definition
            )
            for one in self.allowed
        }
        return LaidDesign(definition=definition, entries=entries)


def domain_owner(domain: DomainData) -> EntityIdentifier:
    return domain.id


def user_owner(user: UserData) -> EntityIdentifier:
    return UserID(user.id)


# --- the merged read ---------------------------------------------------------------


@dataclass(frozen=True)
class AMergeAndACaller:
    """병합해 읽을 이름들과, 그것을 읽을 사람."""

    caller: UserData
    names: tuple[str, ...]


@dataclass(frozen=True)
class AConfigLaidAcross(Given[Any, AMergeAndACaller]):
    """이름 하나에 세 스코프의 조각을 심어 두고, 그 도메인의 사용자 한 명.

    값을 대준 스코프에만 조각이 놓이고, 그 종류의 허용 항목은 조각과 함께 열린다. 다른
    사용자와 다른 도메인의 조각은 같은 이름에 심되 답하지 않으므로, 병합에 섞이면 그 자리에서
    어긋난다.
    """

    public: Mapping[str, Any] | None = None
    domain: Mapping[str, Any] | None = None
    user: Mapping[str, Any] | None = None
    another_user: Mapping[str, Any] | None = None
    another_domain: Mapping[str, Any] | None = None
    also_allowed: tuple[AppConfigScopeType, ...] = ()
    ranks: Mapping[AppConfigScopeType, int] = field(default_factory=dict)
    granted: bool = True
    defined: bool = True
    asked: int = 1

    def _allowed(self) -> tuple[AppConfigScopeType, ...]:
        kinds: list[AppConfigScopeType] = list(self.also_allowed)
        if self.public is not None and AppConfigScopeType.PUBLIC not in kinds:
            kinds.append(AppConfigScopeType.PUBLIC)
        if (self.domain is not None or self.another_domain is not None) and (
            AppConfigScopeType.DOMAIN not in kinds
        ):
            kinds.append(AppConfigScopeType.DOMAIN)
        if (self.user is not None or self.another_user is not None) and (
            AppConfigScopeType.USER not in kinds
        ):
            kinds.append(AppConfigScopeType.USER)
        return tuple(kinds)

    @override
    def describe(self) -> str:
        who = (
            "자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명"
            if self.granted
            else "설정 권한을 하나도 받지 않은 사용자 한 명"
        )
        if not self.defined:
            return f"등록되지 않은 이름과, {who}"
        laid = [SCOPE_NAMES[one] for one in self._allowed()]
        where = "·".join(laid) if laid else "아무 스코프에도 열리지 않은"
        return f"{where} 스코프에 열린 이름 하나와, {who}"

    @override
    async def lay(self, seeding: Any) -> AMergeAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(
            SomeoneGrantedOnTheirOwn(
                home,
                AppConfigEntityType(),
                granted=(Permission.READ,) if self.granted else (),
            )
        )
        if not self.defined:
            return AMergeAndACaller(caller=seeding.made(caller), names=(UNREGISTERED,) * self.asked)
        design = await seeding.within(ADesignOf(allowed=self._allowed(), ranks=self.ranks))
        entries = design.entries
        if self.public is not None:
            await seeding.creating_from(
                SeedPublicFragment(config=self.public), entries[AppConfigScopeType.PUBLIC]
            )
        if self.domain is not None:
            await seeding.creating_from_two(
                SeedFragmentOf(
                    owner_of=domain_owner, config=self.domain, name_hint="domain-fragment"
                ),
                entries[AppConfigScopeType.DOMAIN],
                home,
            )
        if self.user is not None:
            await seeding.creating_from_two(
                SeedFragmentOf(owner_of=user_owner, config=self.user, name_hint="own-fragment"),
                entries[AppConfigScopeType.USER],
                caller,
            )
        if self.another_user is not None:
            other = await seeding.within(SomeoneOf(home))
            await seeding.creating_from_two(
                SeedFragmentOf(
                    owner_of=user_owner, config=self.another_user, name_hint="anothers-fragment"
                ),
                entries[AppConfigScopeType.USER],
                other,
            )
        if self.another_domain is not None:
            away = await seeding.creating(SeedDomain(name_hint="away", description=WAS_HERE))
            await seeding.creating_from_two(
                SeedFragmentOf(
                    owner_of=domain_owner,
                    config=self.another_domain,
                    name_hint="other-domains-fragment",
                ),
                entries[AppConfigScopeType.DOMAIN],
                away,
            )
        name = seeding.made(design.definition).config_name
        return AMergeAndACaller(caller=seeding.made(caller), names=(name,) * self.asked)


@dataclass(frozen=True)
class SeveralConfigsLaid(Given[Any, AMergeAndACaller]):
    """공개 조각을 하나씩 가진 이름 여럿과, 그 도메인의 사용자 한 명."""

    publics: tuple[Mapping[str, Any], ...]
    granted: bool = True

    @override
    def describe(self) -> str:
        who = (
            "자기 스코프에서 설정 읽기 권한을 받은 사용자 한 명"
            if self.granted
            else "설정 권한을 하나도 받지 않은 사용자 한 명"
        )
        return f"공개 조각을 하나씩 가진 이름 {len(self.publics)}개와, {who}"

    @override
    async def lay(self, seeding: Any) -> AMergeAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(
            SomeoneGrantedOnTheirOwn(
                home,
                AppConfigEntityType(),
                granted=(Permission.READ,) if self.granted else (),
            )
        )
        names: list[str] = []
        for config in self.publics:
            design = await seeding.within(ADesignOf(allowed=(AppConfigScopeType.PUBLIC,)))
            await seeding.creating_from(
                SeedPublicFragment(config=config), design.entries[AppConfigScopeType.PUBLIC]
            )
            names.append(seeding.made(design.definition).config_name)
        return AMergeAndACaller(caller=seeding.made(caller), names=tuple(names))


@dataclass(frozen=True)
class TheMergedConfigs(Then[AMergeAndACaller, GetAppConfigsPayload]):
    """요청한 이름마다 하나씩, 요청 순서대로, 병합된 설정이 통째로 온다."""

    wanted: tuple[Mapping[str, Any], ...]

    @override
    def says(self) -> str:
        return "요청한 이름마다 병합된 설정이 온다"

    @override
    def look(
        self, laid: AMergeAndACaller, answered: Answered[GetAppConfigsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("app_configs", len(payload.app_configs), len(self.wanted))]
        for i, (got, wanted) in enumerate(zip(payload.app_configs, self.wanted, strict=False)):
            seen.append(
                Held(
                    f"app_configs[{i}].config_name",
                    got.config_name,
                    SameAs(laid.names[i], "요청한 이름"),
                )
            )
            seen.append(Same(f"app_configs[{i}].config", got.config, dict(wanted)))
        return seen
