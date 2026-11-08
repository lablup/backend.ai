"""What a fair share scenario table says besides the call.

A fair share weight is written against a resource group, so a role sitting on the group
is how a user other than the superadmin reaches it. A table needs the group, the domains
whose weights the call writes, and the caller.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import GlobalEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload,
    DomainFairShareNode,
    ProjectFairShareNode,
    SearchDomainFairSharesPayload,
    SearchProjectFairSharesPayload,
    SearchUserFairSharesPayload,
    UserFairShareNode,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.resource_group import SomeoneGrantedOnTheGroup
from bai_scenario.components.system import role_named
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.fair_share.fair_share import (
    FairShareState,
    TestSeedDomainFairShare,
    TestSeedProjectFairShare,
    TestSeedUserFairShare,
)
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import TestSeedUserPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.user.user import TestSeedUserOf

WEIGHT = Decimal("2.5")


@dataclass(frozen=True)
class DomainsInAGroupAndACaller:
    """리소스 그룹 하나, 가중치를 정할 도메인들, 그리고 호출할 사용자. 첫 도메인이 호출자의 집이다."""

    group: ResourceGroupData
    domains: tuple[DomainData, ...]
    caller: UserData


@dataclass(frozen=True)
class DomainsInAGroupAndSomeone(Given[Any, DomainsInAGroupAndACaller]):
    """그룹 하나와 도메인 ``1 + besides``개, 사용자 한 명. ``granted``를 주면 그 그룹에 앉힌 역할로 그 권한을 받는다."""

    role: UserRole = UserRole.USER
    granted: Permission | None = None
    besides: int = 0

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        if self.granted is not None:
            who_ko = f"그 그룹 범위의 {self.granted.name} 역할을 받은 {who}"
            who_en = (
                f"the {in_language(who, Language.ENGLISH)} granted the {self.granted.name} role "
                "in the resource group scope"
            )
        else:
            who_ko = who
            who_en = f"one {in_language(who, Language.ENGLISH)}"
        return Says(
            f"리소스 그룹 하나와 도메인 {1 + self.besides}개, 그리고 {who_ko} 한 명",
            english=f"one resource group and {1 + self.besides} domains, and {who_en}",
        )

    @override
    async def lay(self, seeding: Any) -> DomainsInAGroupAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        others = [
            await seeding.creating(TestSeedDomain(name_hint="other", description=WAS_HERE))
            for _ in range(self.besides)
        ]
        group = await seeding.creating(TestSeedResourceGroup())
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if self.granted is not None:
            await seeding.within(SomeoneGrantedOnTheGroup(group, caller, self.granted))
        return DomainsInAGroupAndACaller(
            group=seeding.made(group),
            domains=tuple(seeding.made(domain) for domain in (home, *others)),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheDomainWeight(Then[DomainsInAGroupAndACaller, DomainFairShareNode]):
    """첫 도메인의 기록이 정한 가중치를 싣고 온다. 나머지 설정은 그룹 기본값이다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "정한 가중치를 담은 기록이 오고, 나머지 설정은 그룹 기본값입니다",
            english=(
                "the record comes back carrying the weight just set and the rest of the settings "
                "are the group defaults"
            ),
        )

    @override
    def look(
        self, laid: DomainsInAGroupAndACaller, answered: Answered[DomainFairShareNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None)]
        spec = node.spec
        snapshot = node.calculation_snapshot
        written = WrittenByThisRun(self.started)
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Same("resource_group_name", node.resource_group_name, laid.group.name),
            Same("domain_name", node.domain_name, laid.domains[0].name),
            Same("spec.weight", spec.weight, WEIGHT),
            Same("spec.uses_default", spec.uses_default, False),
            Same("spec.half_life_days", spec.half_life_days, 7),
            Same("spec.lookback_days", spec.lookback_days, 28),
            Same("spec.decay_unit_days", spec.decay_unit_days, 1),
            Same("spec.resource_weights", list(spec.resource_weights), []),
            Same("calculation_snapshot.fair_share_factor", snapshot.fair_share_factor, Decimal(1)),
            Same(
                "calculation_snapshot.total_decayed_usage",
                list(snapshot.total_decayed_usage.entries),
                [],
            ),
            Same("calculation_snapshot.normalized_usage", snapshot.normalized_usage, Decimal(0)),
            Skipped(
                "calculation_snapshot.lookback_start",
                Says("쓴 날짜에 따라 달라집니다", english="it depends on the date written"),
            ),
            Skipped(
                "calculation_snapshot.lookback_end",
                Says("쓴 날짜에 따라 달라집니다", english="it depends on the date written"),
            ),
            Held("calculation_snapshot.last_calculated_at", snapshot.last_calculated_at, written),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class EveryWeightIsWritten(Then[DomainsInAGroupAndACaller, BulkUpsertDomainFairShareWeightPayload]):
    """도메인마다 가중치가 정해지고 그 개수가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "도메인 수만큼 정했다는 개수가 옵니다",
            english="a count comes back saying how many domains were set",
        )

    @override
    def look(
        self,
        laid: DomainsInAGroupAndACaller,
        answered: Answered[BulkUpsertDomainFairShareWeightPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        return [Same("upserted_count", payload.upserted_count, len(laid.domains))]


# ------------------------------------------------------------------ reads

type FairShareNode = DomainFairShareNode | ProjectFairShareNode | UserFairShareNode


@dataclass(frozen=True)
class SomeoneGrantedFairSharesOnTheGroup(TestSeedNest[Laid[None]]):
    """그 그룹 범위의 역할로 fair share 권한 하나를 받은 사용자. fair share 는 전역 대상 타입으로 검사한다."""

    group: Laid[ResourceGroupData]
    user: Laid[UserData]
    permission: Permission

    @override
    def kind(self) -> str:
        return Says(
            f"리소스 그룹 범위의 fair share {self.permission.name} 역할을 받은 사용자 준비",
            english=(
                f"Prepare a user granted the fair share {self.permission.name} role in the "
                "resource group scope"
            ),
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda g: ResourceGroupID(g.id), name_hint="fair-share-role"), self.group
        )
        seed.adding(
            TestSeedPermission(entity_type=GlobalEntityType(), permission=self.permission), role
        )
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class AMemberOf(TestSeedNest[Laid[UserData]]):
    """그 도메인의 사용자 한 명. 그 프로젝트의 멤버 목록에 오른다."""

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    name_hint: str = "member"
    status: UserStatus | None = None

    @override
    def kind(self) -> str:
        return Says(
            "프로젝트 멤버 목록에 오른 사용자 한 명 준비",
            english="Prepare one user on the project member list",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        seed.once(TestSeedProjectPolicy())
        policy = seed.creating(TestSeedUserPolicy())
        key_policy = seed.creating(TestSeedKeypairPolicy())
        member = seed.provisioning(
            TestSeedUserOf(name_hint=self.name_hint, status=self.status),
            self.domain,
            policy,
            key_policy,
        )
        seed.joining(
            self.project,
            member,
            project_id=lambda p: ProjectID(p.id),
            user_id=lambda u: UserID(u.id),
        )
        return member


def _granted_caller(permission: Permission) -> Says:
    return Says(
        f"그 그룹 범위의 fair share {permission.name} 역할을 받은 일반 사용자 한 명",
        english=(
            f"one regular user granted the fair share {permission.name} role in the resource "
            "group scope"
        ),
    )


@dataclass(frozen=True)
class AWeightAndACaller[D]:
    """리소스 그룹 하나, 그 그룹에 기록한 fair share 하나, 호출자. ``about``은 기록 대상의 이름이다."""

    group: ResourceGroupData
    record: D
    about: str
    caller: UserData


@dataclass(frozen=True)
class ADomainWeightAndSomeone(Given[Any, AWeightAndACaller[DomainFairShareData]]):
    """호출자의 도메인에 fair share 를 기록한 그룹 하나. 호출자는 그 그룹 범위에서 ``granted``를 받는다."""

    granted: Permission

    @override
    def describe(self) -> str:
        who = _granted_caller(self.granted)
        return Says(
            f"리소스 그룹 하나와 그 그룹에 fair share 를 기록한 도메인 하나, 그리고 {who}",
            english=(
                "one resource group and one domain whose fair share is recorded in it, and "
                f"{who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AWeightAndACaller[DomainFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(SomeoneGrantedFairSharesOnTheGroup(group, caller, self.granted))
        record = await seeding.adding(
            TestSeedDomainFairShare(domain_name=seeding.made(home).name), group
        )
        return AWeightAndACaller(
            group=seeding.made(group),
            record=seeding.made(record),
            about=seeding.made(home).name,
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AProjectWeightAndSomeone(Given[Any, AWeightAndACaller[ProjectFairShareData]]):
    """fair share 를 그 그룹에 기록한 프로젝트 하나. 호출자는 그 그룹 범위에서 ``granted``를 받는다."""

    granted: Permission

    @override
    def describe(self) -> str:
        who = _granted_caller(self.granted)
        return Says(
            f"리소스 그룹 하나와 그 그룹에 fair share 를 기록한 프로젝트 하나, 그리고 {who}",
            english=(
                "one resource group and one project whose fair share is recorded in it, and "
                f"{who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AWeightAndACaller[ProjectFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), home, policy)
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(SomeoneGrantedFairSharesOnTheGroup(group, caller, self.granted))
        made = seeding.made(project)
        record = await seeding.adding(
            TestSeedProjectFairShare(
                project_name=made.name, project_id=made.id, domain_name=made.domain_name
            ),
            group,
        )
        return AWeightAndACaller(
            group=seeding.made(group),
            record=seeding.made(record),
            about=made.name,
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AUserWeightAndSomeone(Given[Any, AWeightAndACaller[UserFairShareData]]):
    """프로젝트 멤버 한 명의 fair share 를 그 그룹에 기록했다. 호출자는 그 그룹 범위에서 ``granted``를 받는다."""

    granted: Permission

    @override
    def describe(self) -> str:
        who = _granted_caller(self.granted)
        return Says(
            (
                "리소스 그룹 하나와 프로젝트 하나, 그 그룹에 fair share 를 기록한 프로젝트 멤버 "
                f"하나, 그리고 {who}"
            ),
            english=(
                "one resource group, one project and one project member whose fair share is "
                f"recorded in the group, and {who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AWeightAndACaller[UserFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), home, policy)
        member = await seeding.within(AMemberOf(home, project))
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(SomeoneGrantedFairSharesOnTheGroup(group, caller, self.granted))
        made_project = seeding.made(project)
        made_member = seeding.made(member)
        record = await seeding.adding(
            TestSeedUserFairShare(
                username=made_member.username,
                user_uuid=made_member.id,
                project_name=made_project.name,
                project_id=made_project.id,
                domain_name=made_project.domain_name,
            ),
            group,
        )
        return AWeightAndACaller(
            group=seeding.made(group),
            record=seeding.made(record),
            about=made_member.username,
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class FairShareLook:
    """fair share 노드 하나의 설정과 계산값이 어떤 값으로 와야 하는지."""

    started: datetime
    at: str = ""

    def recorded(self, node: FairShareNode, state: FairShareState) -> list[Verdict]:
        """시드한 기록의 값이 그대로 온다."""
        spec = node.spec
        snapshot = node.calculation_snapshot
        written = WrittenByThisRun(self.started)
        at = self.at
        return [
            Same(f"{at}spec.weight", spec.weight, state.weight),
            Same(f"{at}spec.uses_default", spec.uses_default, False),
            Same(f"{at}spec.half_life_days", spec.half_life_days, state.half_life_days),
            Same(f"{at}spec.lookback_days", spec.lookback_days, state.lookback_days),
            Same(f"{at}spec.decay_unit_days", spec.decay_unit_days, state.decay_unit_days),
            Same(f"{at}spec.resource_weights", list(spec.resource_weights), []),
            Same(
                f"{at}calculation_snapshot.fair_share_factor",
                snapshot.fair_share_factor,
                state.fair_share_factor,
            ),
            Same(
                f"{at}calculation_snapshot.total_decayed_usage",
                [(e.resource_type, e.quantity) for e in snapshot.total_decayed_usage.entries],
                [(name, Decimal(value)) for name, value in state.total_decayed_usage.items()],
            ),
            Same(
                f"{at}calculation_snapshot.normalized_usage",
                snapshot.normalized_usage,
                state.normalized_usage,
            ),
            Same(
                f"{at}calculation_snapshot.lookback_start",
                snapshot.lookback_start,
                state.lookback_start,
            ),
            Same(
                f"{at}calculation_snapshot.lookback_end", snapshot.lookback_end, state.lookback_end
            ),
            Held(
                f"{at}calculation_snapshot.last_calculated_at", snapshot.last_calculated_at, written
            ),
            Held(f"{at}created_at", node.created_at, written),
            Held(f"{at}updated_at", node.updated_at, written),
        ]

    def defaulted(self, node: FairShareNode, group: ResourceGroupData) -> list[Verdict]:
        """기록이 없으면 그룹의 기본값과 사용량이 없는 계산값이 온다."""
        spec = node.spec
        snapshot = node.calculation_snapshot
        defaults = group.fair_share_spec
        written = WrittenByThisRun(self.started)
        at = self.at
        by_date = Says(
            "요청한 날짜에 따라 달라집니다", english="it depends on the date of the request"
        )
        return [
            Same(f"{at}spec.weight", spec.weight, defaults.default_weight),
            Same(f"{at}spec.uses_default", spec.uses_default, True),
            Same(f"{at}spec.half_life_days", spec.half_life_days, defaults.half_life_days),
            Same(f"{at}spec.lookback_days", spec.lookback_days, defaults.lookback_days),
            Same(f"{at}spec.decay_unit_days", spec.decay_unit_days, defaults.decay_unit_days),
            Same(f"{at}spec.resource_weights", list(spec.resource_weights), []),
            Same(
                f"{at}calculation_snapshot.fair_share_factor",
                snapshot.fair_share_factor,
                Decimal(1),
            ),
            Same(
                f"{at}calculation_snapshot.total_decayed_usage",
                list(snapshot.total_decayed_usage.entries),
                [],
            ),
            Same(
                f"{at}calculation_snapshot.normalized_usage",
                snapshot.normalized_usage,
                Decimal(0),
            ),
            Skipped(f"{at}calculation_snapshot.lookback_start", by_date),
            Skipped(f"{at}calculation_snapshot.lookback_end", by_date),
            Held(
                f"{at}calculation_snapshot.last_calculated_at", snapshot.last_calculated_at, written
            ),
            Held(f"{at}created_at", node.created_at, written),
            Held(f"{at}updated_at", node.updated_at, written),
        ]


def _joined_key(group: ResourceGroupData, *ids: UUID) -> SameAs[str]:
    return SameAs(
        ":".join([group.name, *(str(one) for one in ids)]),
        Says(
            "리소스 그룹 이름과 기록 대상의 id 를 콜론으로 이은 값",
            english="the resource group name and the ids of what the record is about, joined by colons",
        ),
    )


def _the_seeded(what: str, english: str) -> Says:
    return Says(f"시드한 {what}의 id", english=f"the id of the seeded {english}")


@dataclass(frozen=True)
class TheDomainRecord(Then[AWeightAndACaller[DomainFairShareData], DomainFairShareNode | None]):
    """그룹에 기록한 도메인의 fair share 가 시드한 값 그대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 도메인의 fair share 기록이 시드한 값 그대로 옵니다",
            english="the fair share record of that domain comes back with the seeded values",
        )

    @override
    def look(
        self,
        laid: AWeightAndACaller[DomainFairShareData],
        answered: Answered[DomainFairShareNode | None],
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None), Same("item.present", False, True)]
        return DomainRecordLook(self.started).of(node, laid.group, laid.record)


@dataclass(frozen=True)
class TheProjectRecord(Then[AWeightAndACaller[ProjectFairShareData], ProjectFairShareNode | None]):
    """그룹에 기록한 프로젝트의 fair share 가 시드한 값 그대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 프로젝트의 fair share 기록이 시드한 값 그대로 옵니다",
            english="the fair share record of that project comes back with the seeded values",
        )

    @override
    def look(
        self,
        laid: AWeightAndACaller[ProjectFairShareData],
        answered: Answered[ProjectFairShareNode | None],
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None), Same("item.present", False, True)]
        return ProjectRecordLook(self.started).of(node, laid.group, laid.record)


@dataclass(frozen=True)
class ProjectRecordLook:
    """시드한 프로젝트 기록 하나가 노드로 어떻게 와야 하는지."""

    started: datetime
    at: str = ""

    def of(
        self, node: ProjectFairShareNode, group: ResourceGroupData, record: ProjectFairShareData
    ) -> list[Verdict]:
        at = self.at
        return [
            Held(f"{at}id", node.id, _joined_key(group, record.project_id)),
            Same(f"{at}resource_group_name", node.resource_group_name, group.name),
            Held(
                f"{at}project_id",
                node.project_id,
                SameAs(record.project_id, _the_seeded("프로젝트", "project")),
            ),
            Same(f"{at}domain_name", node.domain_name, record.domain_name),
            *FairShareLook(self.started, at).recorded(node, FairShareState()),
        ]


@dataclass(frozen=True)
class UserRecordLook:
    """시드한 사용자 기록 하나가 노드로 어떻게 와야 하는지."""

    started: datetime
    at: str = ""

    def of(
        self, node: UserFairShareNode, group: ResourceGroupData, record: UserFairShareData
    ) -> list[Verdict]:
        at = self.at
        return [
            Held(f"{at}id", node.id, _joined_key(group, record.user_uuid, record.project_id)),
            Same(f"{at}resource_group_name", node.resource_group_name, group.name),
            Held(
                f"{at}user_uuid",
                node.user_uuid,
                SameAs(record.user_uuid, _the_seeded("사용자", "user")),
            ),
            Held(
                f"{at}project_id",
                node.project_id,
                SameAs(record.project_id, _the_seeded("프로젝트", "project")),
            ),
            Same(f"{at}domain_name", node.domain_name, record.domain_name),
            *FairShareLook(self.started, at).recorded(node, FairShareState()),
        ]


@dataclass(frozen=True)
class TheUserRecord(Then[AWeightAndACaller[UserFairShareData], UserFairShareNode | None]):
    """그룹에 기록한 프로젝트 멤버의 fair share 가 시드한 값 그대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 멤버의 fair share 기록이 시드한 값 그대로 옵니다",
            english="the fair share record of that member comes back with the seeded values",
        )

    @override
    def look(
        self,
        laid: AWeightAndACaller[UserFairShareData],
        answered: Answered[UserFairShareNode | None],
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("raised", answered.raised, None), Same("item.present", False, True)]
        return UserRecordLook(self.started).of(node, laid.group, laid.record)


@dataclass(frozen=True)
class DomainRecordLook:
    """시드한 도메인 기록 하나가 노드로 어떻게 와야 하는지."""

    started: datetime
    at: str = ""

    def of(
        self, node: DomainFairShareNode, group: ResourceGroupData, record: DomainFairShareData
    ) -> list[Verdict]:
        at = self.at
        return [
            Same(f"{at}id", node.id, f"{group.name}:{record.domain_name}"),
            Same(f"{at}resource_group_name", node.resource_group_name, group.name),
            Same(f"{at}domain_name", node.domain_name, record.domain_name),
            *FairShareLook(self.started, at).recorded(node, FairShareState()),
        ]


@dataclass(frozen=True)
class WeightsInTwoGroupsAndACaller[D]:
    """리소스 그룹 둘에 기록한 fair share 들과 호출자. ``first``는 ``group``의 기록 둘 가운데 이름 순으로 앞선 것이다."""

    group: ResourceGroupData
    first: D
    caller: UserData


def _who_by_role(role: UserRole) -> Says:
    who = role_named(role)
    return Says(f"{who} 한 명", english=f"one {in_language(who, Language.ENGLISH)}")


@dataclass(frozen=True)
class DomainWeightsInTwoGroups(Given[Any, WeightsInTwoGroupsAndACaller[DomainFairShareData]]):
    """그룹에 도메인 둘의 기록, 다른 그룹에 첫 도메인의 기록 하나."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = _who_by_role(self.role)
        return Says(
            (
                "리소스 그룹 하나에 도메인 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 도메인의 "
                f"fair share 를 기록했고, {who}"
            ),
            english=(
                "the fair shares of two domains are recorded in one resource group and that of "
                f"one of them in another resource group, and {who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> WeightsInTwoGroupsAndACaller[DomainFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        other = await seeding.creating(TestSeedDomain(name_hint="other", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        elsewhere = await seeding.creating(TestSeedResourceGroup(name_hint="elsewhere"))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        first = await seeding.adding(
            TestSeedDomainFairShare(domain_name=seeding.made(home).name), group
        )
        await seeding.adding(TestSeedDomainFairShare(domain_name=seeding.made(other).name), group)
        await seeding.adding(
            TestSeedDomainFairShare(domain_name=seeding.made(home).name), elsewhere
        )
        return WeightsInTwoGroupsAndACaller(
            group=seeding.made(group), first=seeding.made(first), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class ProjectWeightsInTwoGroups(Given[Any, WeightsInTwoGroupsAndACaller[ProjectFairShareData]]):
    """그룹에 프로젝트 둘의 기록, 다른 그룹에 첫 프로젝트의 기록 하나."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = _who_by_role(self.role)
        return Says(
            (
                "리소스 그룹 하나에 프로젝트 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 "
                f"프로젝트의 fair share 를 기록했고, {who}"
            ),
            english=(
                "the fair shares of two projects are recorded in one resource group and that of "
                f"one of them in another resource group, and {who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> WeightsInTwoGroupsAndACaller[ProjectFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        elsewhere = await seeding.creating(TestSeedResourceGroup(name_hint="elsewhere"))
        policy = await seeding.once(TestSeedProjectPolicy())
        alpha = await seeding.creating_from_two(TestSeedProject(name_hint="alpha"), home, policy)
        beta = await seeding.creating_from_two(TestSeedProject(name_hint="beta"), home, policy)
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        records = [
            await seeding.adding(
                TestSeedProjectFairShare(
                    project_name=made.name, project_id=made.id, domain_name=made.domain_name
                ),
                where,
            )
            for made, where in (
                (seeding.made(alpha), group),
                (seeding.made(beta), group),
                (seeding.made(alpha), elsewhere),
            )
        ]
        return WeightsInTwoGroupsAndACaller(
            group=seeding.made(group), first=seeding.made(records[0]), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class UserWeightsInTwoGroups(Given[Any, WeightsInTwoGroupsAndACaller[UserFairShareData]]):
    """그룹에 프로젝트 멤버 둘의 기록, 다른 그룹에 첫 멤버의 기록 하나."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = _who_by_role(self.role)
        return Says(
            (
                "리소스 그룹 하나에 프로젝트 멤버 둘의 fair share, 다른 리소스 그룹에 그 가운데 한 "
                f"멤버의 fair share 를 기록했고, {who}"
            ),
            english=(
                "the fair shares of two project members are recorded in one resource group and "
                f"that of one of them in another resource group, and {who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> WeightsInTwoGroupsAndACaller[UserFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        elsewhere = await seeding.creating(TestSeedResourceGroup(name_hint="elsewhere"))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), home, policy)
        alpha = await seeding.within(AMemberOf(home, project, name_hint="alpha"))
        beta = await seeding.within(AMemberOf(home, project, name_hint="beta"))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        made_project = seeding.made(project)
        records = [
            await seeding.adding(
                TestSeedUserFairShare(
                    username=made.username,
                    user_uuid=made.id,
                    project_name=made_project.name,
                    project_id=made_project.id,
                    domain_name=made_project.domain_name,
                ),
                where,
            )
            for made, where in (
                (seeding.made(alpha), group),
                (seeding.made(beta), group),
                (seeding.made(alpha), elsewhere),
            )
        ]
        return WeightsInTwoGroupsAndACaller(
            group=seeding.made(group), first=seeding.made(records[0]), caller=seeding.made(caller)
        )


def _one_page_of_two(total_count: int, items: Sequence[Any]) -> list[Verdict]:
    return [Same("total_count", total_count, 2), Same("items.count", len(items), 1)]


@dataclass(frozen=True)
class TheFirstDomainOfTheGroup(
    Then[WeightsInTwoGroupsAndACaller[DomainFairShareData], SearchDomainFairSharesPayload]
):
    """그룹의 기록 둘이 세어지고, 이름 순 첫 기록 하나만 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 도메인의 기록 하나만 옵니다",
            english=(
                "the two records of that group are counted and only the record of the domain "
                "first by name comes back"
            ),
        )

    @override
    def look(
        self,
        laid: WeightsInTwoGroupsAndACaller[DomainFairShareData],
        answered: Answered[SearchDomainFairSharesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        page = _one_page_of_two(payload.total_count, payload.items)
        if len(payload.items) != 1:
            return page
        look = DomainRecordLook(self.started, "items[0].")
        return [*page, *look.of(payload.items[0], laid.group, laid.first)]


@dataclass(frozen=True)
class TheFirstProjectOfTheGroup(
    Then[WeightsInTwoGroupsAndACaller[ProjectFairShareData], SearchProjectFairSharesPayload]
):
    """그룹의 기록 둘이 세어지고, 이름 순 첫 기록 하나만 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 그룹의 기록 둘이 세어지고 이름 순으로 앞선 프로젝트의 기록 하나만 옵니다",
            english=(
                "the two records of that group are counted and only the record of the project "
                "first by name comes back"
            ),
        )

    @override
    def look(
        self,
        laid: WeightsInTwoGroupsAndACaller[ProjectFairShareData],
        answered: Answered[SearchProjectFairSharesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        page = _one_page_of_two(payload.total_count, payload.items)
        if len(payload.items) != 1:
            return page
        look = ProjectRecordLook(self.started, "items[0].")
        return [*page, *look.of(payload.items[0], laid.group, laid.first)]


@dataclass(frozen=True)
class TheFirstUserOfTheGroup(
    Then[WeightsInTwoGroupsAndACaller[UserFairShareData], SearchUserFairSharesPayload]
):
    """그룹의 기록 둘이 세어지고, 이름 순 첫 기록 하나만 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 그룹의 기록 둘이 세어지고 사용자 이름 순으로 앞선 멤버의 기록 하나만 옵니다",
            english=(
                "the two records of that group are counted and only the record of the member "
                "first by username comes back"
            ),
        )

    @override
    def look(
        self,
        laid: WeightsInTwoGroupsAndACaller[UserFairShareData],
        answered: Answered[SearchUserFairSharesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        page = _one_page_of_two(payload.total_count, payload.items)
        if len(payload.items) != 1:
            return page
        look = UserRecordLook(self.started, "items[0].")
        return [*page, *look.of(payload.items[0], laid.group, laid.first)]


# ------------------------------------------------------------------ searches in one group


@dataclass(frozen=True)
class DomainsAroundAGroupAndACaller:
    """리소스 그룹 하나, 두 번째 쪽에 올 도메인, 호출자."""

    group: ResourceGroupData
    paged: DomainData
    caller: UserData


@dataclass(frozen=True)
class DomainsAndAWeightElsewhere(Given[Any, DomainsAroundAGroupAndACaller]):
    """활성 도메인 둘과 비활성 도메인 하나. 둘째 활성 도메인의 기록은 다른 그룹에만 있다."""

    granted: Permission

    @override
    def describe(self) -> str:
        who = _granted_caller(self.granted)
        return Says(
            (
                "리소스 그룹 둘, 활성 도메인 둘과 비활성 도메인 하나, 그 가운데 한 활성 도메인의 "
                f"fair share 는 다른 리소스 그룹에만 기록했고, {who}"
            ),
            english=(
                "two resource groups, two active domains and one inactive domain, the fair share "
                f"of one active domain recorded only in the other resource group, and {who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> DomainsAroundAGroupAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        other = await seeding.creating(TestSeedDomain(name_hint="other", description=WAS_HERE))
        await seeding.creating(
            TestSeedDomain(name_hint="dormant", description=WAS_HERE, is_active=False)
        )
        group = await seeding.creating(TestSeedResourceGroup())
        elsewhere = await seeding.creating(TestSeedResourceGroup(name_hint="elsewhere"))
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(SomeoneGrantedFairSharesOnTheGroup(group, caller, self.granted))
        await seeding.adding(
            TestSeedDomainFairShare(domain_name=seeding.made(other).name), elsewhere
        )
        return DomainsAroundAGroupAndACaller(
            group=seeding.made(group), paged=seeding.made(other), caller=seeding.made(caller)
        )


@dataclass(frozen=True)
class TheSecondActiveDomainOnItsDefaults(
    Then[DomainsAroundAGroupAndACaller, SearchDomainFairSharesPayload]
):
    """활성 도메인 둘이 세어지고, 둘째 쪽 도메인은 다른 그룹의 기록 대신 그룹 기본값으로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            (
                "활성 도메인 둘이 세어지고, 둘째 도메인은 다른 리소스 그룹의 기록이 아니라 이 그룹의 "
                "기본값으로 옵니다"
            ),
            english=(
                "the two active domains are counted, and the second domain comes back with this "
                "group's defaults rather than the record in the other resource group"
            ),
        )

    @override
    def look(
        self, laid: DomainsAroundAGroupAndACaller, answered: Answered[SearchDomainFairSharesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        page = _one_page_of_two(payload.total_count, payload.items)
        if len(payload.items) != 1:
            return page
        node = payload.items[0]
        return [
            *page,
            Same("items[0].id", node.id, f"{laid.group.name}:{laid.paged.name}"),
            Same("items[0].resource_group_name", node.resource_group_name, laid.group.name),
            Same("items[0].domain_name", node.domain_name, laid.paged.name),
            *FairShareLook(self.started, "items[0].").defaulted(node, laid.group),
        ]


@dataclass(frozen=True)
class AScopedWeightAndACaller[D]:
    """리소스 그룹 하나, 검색할 도메인과 프로젝트, 둘째 쪽에 올 기록, 호출자."""

    group: ResourceGroupData
    domain: DomainData
    project: ProjectData
    record: D
    caller: UserData


@dataclass(frozen=True)
class ProjectsAroundADomain(Given[Any, AScopedWeightAndACaller[ProjectFairShareData]]):
    """도메인 안 활성 프로젝트 둘과 비활성 프로젝트 하나, 다른 도메인의 프로젝트 하나. 둘째 활성 프로젝트에 기록이 있다."""

    granted: Permission

    @override
    def describe(self) -> str:
        who = _granted_caller(self.granted)
        return Says(
            (
                "리소스 그룹 하나, 도메인 안 활성 프로젝트 둘과 비활성 프로젝트 하나, 다른 도메인의 "
                f"프로젝트 하나, 활성 프로젝트 하나의 fair share 를 그 그룹에 기록했고, {who}"
            ),
            english=(
                "one resource group, two active projects and one inactive project in the domain, "
                "one project in another domain, the fair share of one active project recorded in "
                f"the group, and {who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AScopedWeightAndACaller[ProjectFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        far = await seeding.creating(TestSeedDomain(name_hint="far", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        policy = await seeding.once(TestSeedProjectPolicy())
        await seeding.creating_from_two(TestSeedProject(name_hint="alpha"), home, policy)
        beta = await seeding.creating_from_two(TestSeedProject(name_hint="beta"), home, policy)
        await seeding.creating_from_two(
            TestSeedProject(name_hint="dormant", is_active=False), home, policy
        )
        await seeding.creating_from_two(TestSeedProject(name_hint="aside"), far, policy)
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(SomeoneGrantedFairSharesOnTheGroup(group, caller, self.granted))
        made = seeding.made(beta)
        record = await seeding.adding(
            TestSeedProjectFairShare(
                project_name=made.name, project_id=made.id, domain_name=made.domain_name
            ),
            group,
        )
        return AScopedWeightAndACaller(
            group=seeding.made(group),
            domain=seeding.made(home),
            project=made,
            record=seeding.made(record),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class MembersAroundAProject(Given[Any, AScopedWeightAndACaller[UserFairShareData]]):
    """프로젝트의 활성 멤버 둘과 비활성 멤버 하나, 다른 프로젝트의 멤버 하나. 둘째 활성 멤버에 기록이 있다."""

    granted: Permission

    @override
    def describe(self) -> str:
        who = _granted_caller(self.granted)
        return Says(
            (
                "리소스 그룹 하나, 프로젝트의 활성 멤버 둘과 비활성 멤버 하나, 다른 프로젝트의 멤버 "
                f"하나, 활성 멤버 하나의 fair share 를 그 그룹에 기록했고, {who}"
            ),
            english=(
                "one resource group, two active members and one inactive member of the project, "
                "one member of another project, the fair share of one active member recorded in "
                f"the group, and {who.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AScopedWeightAndACaller[UserFairShareData]:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(TestSeedResourceGroup())
        policy = await seeding.once(TestSeedProjectPolicy())
        team = await seeding.creating_from_two(TestSeedProject(name_hint="team"), home, policy)
        aside = await seeding.creating_from_two(TestSeedProject(name_hint="aside"), home, policy)
        await seeding.within(AMemberOf(home, team, name_hint="alpha"))
        beta = await seeding.within(AMemberOf(home, team, name_hint="beta"))
        await seeding.within(AMemberOf(home, team, name_hint="dormant", status=UserStatus.INACTIVE))
        await seeding.within(AMemberOf(home, aside, name_hint="outsider"))
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(SomeoneGrantedFairSharesOnTheGroup(group, caller, self.granted))
        made_team = seeding.made(team)
        made_beta = seeding.made(beta)
        record = await seeding.adding(
            TestSeedUserFairShare(
                username=made_beta.username,
                user_uuid=made_beta.id,
                project_name=made_team.name,
                project_id=made_team.id,
                domain_name=made_team.domain_name,
            ),
            group,
        )
        return AScopedWeightAndACaller(
            group=seeding.made(group),
            domain=seeding.made(home),
            project=made_team,
            record=seeding.made(record),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheSecondActiveProject(
    Then[AScopedWeightAndACaller[ProjectFairShareData], SearchProjectFairSharesPayload]
):
    """도메인 안 활성 프로젝트 둘이 세어지고, 둘째 쪽에 기록한 프로젝트가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            (
                "그 도메인의 활성 프로젝트 둘이 세어지고, 둘째 쪽에 fair share 를 기록한 프로젝트가 "
                "시드한 값 그대로 옵니다"
            ),
            english=(
                "the two active projects of that domain are counted, and the second one comes "
                "back with its recorded fair share"
            ),
        )

    @override
    def look(
        self,
        laid: AScopedWeightAndACaller[ProjectFairShareData],
        answered: Answered[SearchProjectFairSharesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        page = _one_page_of_two(payload.total_count, payload.items)
        if len(payload.items) != 1:
            return page
        look = ProjectRecordLook(self.started, "items[0].")
        return [*page, *look.of(payload.items[0], laid.group, laid.record)]


@dataclass(frozen=True)
class TheSecondActiveMember(
    Then[AScopedWeightAndACaller[UserFairShareData], SearchUserFairSharesPayload]
):
    """프로젝트의 활성 멤버 둘이 세어지고, 둘째 쪽에 기록한 멤버가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            (
                "그 프로젝트의 활성 멤버 둘이 세어지고, 둘째 쪽에 fair share 를 기록한 멤버가 "
                "시드한 값 그대로 옵니다"
            ),
            english=(
                "the two active members of that project are counted, and the second one comes "
                "back with their recorded fair share"
            ),
        )

    @override
    def look(
        self,
        laid: AScopedWeightAndACaller[UserFairShareData],
        answered: Answered[SearchUserFairSharesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Same("raised", answered.raised, None)]
        page = _one_page_of_two(payload.total_count, payload.items)
        if len(payload.items) != 1:
            return page
        look = UserRecordLook(self.started, "items[0].")
        return [*page, *look.of(payload.items[0], laid.group, laid.record)]
