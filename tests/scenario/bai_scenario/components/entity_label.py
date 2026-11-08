"""What an entity label scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. Labels go on domains here: a label answers to the entity it
is on, and a domain is the entity a caller is granted on with the fewest rows.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.entity_label.response import EntityLabelNode
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Skipped,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.entity_label.entity_label import TestSeedDomainLabel
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

LABELED = "domain"
"""라벨이 붙는 엔티티 타입의 이름. 요청이 타입을 이 이름으로 적는다."""

UNWIRED = "no-such-entity-type"
"""아무것도 배선되지 않은 엔티티 타입의 이름."""


@dataclass(frozen=True)
class LabeledDomainsAndACaller:
    """라벨을 붙이거나 뗄 도메인들, 그 위에 미리 붙인 라벨들, 그리고 부를 사람."""

    targets: tuple[DomainData, ...]
    labels: tuple[EntityLabelData, ...]
    caller: UserData


@dataclass(frozen=True)
class WritingDomains(TestSeedNest[Laid[None]]):
    """그 도메인을 읽고 수정할 수 있는 역할을 받는다.

    라벨을 뗄 때 라벨의 주인을 먼저 읽으므로 조회 권한이 함께 필요하다.
    """

    domain: Laid[DomainData]
    user: Laid[UserData]

    @override
    def kind(self) -> str:
        return Says(
            "도메인 수정 권한을 받은 사용자 준비",
            english="Prepare a user granted permission to update the domain",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda d: d.id, name_hint="domain-writer"), self.domain
        )
        for one in (Permission.READ, Permission.UPDATE):
            seed.adding(TestSeedPermission(entity_type=DomainEntityType(), permission=one), role)
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class ReadingDomains(TestSeedNest[Laid[None]]):
    """그 도메인을 읽을 수 있는 역할을 받는다."""

    domain: Laid[DomainData]
    user: Laid[UserData]

    @override
    def kind(self) -> str:
        return Says(
            "도메인 조회 권한을 받은 사용자 준비",
            english="Prepare a user granted permission to read the domain",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda d: d.id, name_hint="domain-reader"), self.domain
        )
        seed.adding(
            TestSeedPermission(entity_type=DomainEntityType(), permission=Permission.READ), role
        )
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class LabeledDomainsAndSomeone(Given[Any, LabeledDomainsAndACaller]):
    """대상 도메인 여럿과, 다른 도메인에 사는 사용자 한 명.

    ``writable``은 앞에서부터 몇 개의 대상에 수정 권한을 받는지, ``readable``은 몇 개를
    읽을 수 있는지, ``keys``는 대상마다 미리 붙여 둘 라벨의 키다. ``elsewhere``는 범위에
    대지 않지만 읽을 수 있는 도메인 수다.
    """

    targets: int = 2
    writable: int = 0
    readable: int = 0
    elsewhere: int = 0
    keys: Sequence[str] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        role = self.role.value
        labeled = f"라벨 {len(self.keys)}개씩 붙은 " if self.keys else ""
        granted = f"그중 {self.writable}개에 수정 권한을 받은 " if self.writable else ""
        reader = f"그중 {self.readable}개를 읽을 수 있는 " if self.readable else ""
        outside = (
            f"범위에 대지 않는 도메인 {self.elsewhere}개도 읽을 수 있는 " if self.elsewhere else ""
        )
        english = (
            f"{self.targets} domains"
            + (f" with {len(self.keys)} labels each" if self.keys else "")
            + f" and one {role}"
            + (f" granted permission to update {self.writable} of them" if self.writable else "")
            + (f" who can read {self.readable} of them" if self.readable else "")
            + (f" and {self.elsewhere} domains outside the scope" if self.elsewhere else "")
        )
        return Says(
            f"{labeled}도메인 {self.targets}개와, {granted}{reader}{outside}{role} 한 명",
            english=english,
        )

    @override
    async def lay(self, seeding: Any) -> LabeledDomainsAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        targets = [
            await seeding.creating(TestSeedDomain(name_hint="target", description=WAS_HERE))
            for _ in range(self.targets)
        ]
        labels = [
            await seeding.adding(TestSeedDomainLabel(key=key, value="before"), target)
            for target in targets
            for key in self.keys
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        for target in targets[: self.writable]:
            await seeding.within(WritingDomains(target, caller))
        for target in targets[: self.readable]:
            await seeding.within(ReadingDomains(target, caller))
        for _ in range(self.elsewhere):
            outside = await seeding.creating(
                TestSeedDomain(name_hint="elsewhere", description=WAS_HERE)
            )
            for key in self.keys:
                await seeding.adding(TestSeedDomainLabel(key=key, value="before"), outside)
            await seeding.within(ReadingDomains(outside, caller))
        return LabeledDomainsAndACaller(
            targets=tuple(seeding.made(one) for one in targets),
            labels=tuple(seeding.made(one) for one in labels),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class LabelLook:
    """라벨 노드가 어떤 값으로 와야 하는지. 붙은 도메인은 미리 만든 것에서 읽는다."""

    started: datetime

    def verdicts(
        self,
        prefix: str,
        node: EntityLabelNode,
        on: DomainData,
        key: str,
        value: str,
        laid: EntityLabelData | None = None,
    ) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        verdicts: list[Verdict] = [
            Same(f"{prefix}entity_type", node.entity_type, LABELED),
            Held[UUID](
                f"{prefix}entity_id",
                node.entity_id,
                SameAs(on.id, Says("대상 도메인의 id", english="the id of the target domain")),
            ),
            Same(f"{prefix}key", node.key, key),
            Same(f"{prefix}value", node.value, value),
            Held(f"{prefix}created_at", node.created_at, written),
            Held(f"{prefix}updated_at", node.updated_at, written),
        ]
        if laid is None:
            return [
                *verdicts,
                Skipped(
                    f"{prefix}id",
                    Says("데이터베이스가 생성합니다", english="the database generates it"),
                ),
                Held[UUID](
                    f"{prefix}field_id",
                    node.field_id,
                    SameAs(node.id, Says("라벨 id", english="the label id")),
                ),
            ]
        return [
            *verdicts,
            Held[UUID](
                f"{prefix}id",
                node.id,
                SameAs(
                    laid.id,
                    Says(
                        "미리 붙인 라벨의 id",
                        english="the id of the label attached in advance",
                    ),
                ),
            ),
            Held[UUID](
                f"{prefix}field_id",
                node.field_id,
                SameAs(
                    laid.id,
                    Says(
                        "미리 붙인 라벨의 id",
                        english="the id of the label attached in advance",
                    ),
                ),
            ),
        ]
