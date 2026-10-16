"""What a HuggingFace registry scenario table says besides the call.

A registry is created in the global scope and reached afterwards by id. A table needs
the caller, the permission the caller was given on artifact registries, and the
registry or registries the call names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    HuggingFaceRegistryNode,
    PurgeHuggingFaceRegistryPayload,
)
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.system import role_named
from bai_scenario.seeds.artifact_registry.registry import TestSeedHuggingFaceRegistry
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

EDITED_URL = "https://hub.example.com"
"""수정 요청이 넣는 새 주소."""

type Edited = PartialBulkPayload[HuggingFaceRegistryNode]
type Purged = PartialBulkPayload[PurgeHuggingFaceRegistryPayload]


@dataclass(frozen=True)
class ARegistryAndACaller:
    """레지스트리 하나와, 그것을 호출할 사용자."""

    registry: HuggingFaceRegistryData
    caller: UserData


@dataclass(frozen=True)
class ManyRegistriesAndACaller:
    """레지스트리 여럿과, 그것들을 한 번에 호출할 사용자."""

    laid: tuple[HuggingFaceRegistryData, ...]
    caller: UserData


@dataclass(frozen=True)
class SomeoneGrantedOnRegistries(TestSeedNest[Laid[UserData]]):
    """그 사용자에게 global 에서 아티팩트 레지스트리에 대한 권한을 준다."""

    domain: Laid[Any]
    granted: tuple[Permission, ...]
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return "global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.GLOBAL), name_hint="registry-keeper"
            ),
            someone,
        )
        for permission in self.granted:
            seed.adding(
                TestSeedPermission(entity_type=ArtifactRegistryEntityType(), permission=permission),
                role,
            )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def lay_a_caller(
    seeding: Any, role: UserRole, granted: tuple[Permission, ...]
) -> Laid[UserData]:
    """A user of the given role, granted the given permissions on artifact registries."""
    home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
    if not granted:
        caller: Laid[UserData] = await seeding.within(SomeoneOf(home, role=role))
        return caller
    granted_caller: Laid[UserData] = await seeding.within(
        SomeoneGrantedOnRegistries(home, granted, role=role)
    )
    return granted_caller


def _holding(role: UserRole, granted: tuple[Permission, ...]) -> str:
    if role == UserRole.SUPERADMIN:
        return f"{role_named(role)} 한 명"
    if not granted:
        return f"아무 권한도 받지 않은 {role_named(role)} 한 명"
    names = ", ".join(str(permission.name) for permission in granted)
    return f"레지스트리에 {names} 권한을 받은 {role_named(role)} 한 명"


@dataclass(frozen=True)
class ARegistryAndSomeone(Given[Any, ARegistryAndACaller]):
    """레지스트리 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        return f"HuggingFace 레지스트리 하나와, {_holding(self.role, self.granted)}"

    @override
    async def lay(self, seeding: Any) -> ARegistryAndACaller:
        registry = await seeding.creating(TestSeedHuggingFaceRegistry(name_hint="registry"))
        caller = await lay_a_caller(seeding, self.role, self.granted)
        return ARegistryAndACaller(seeding.made(registry), seeding.made(caller))


@dataclass(frozen=True)
class ManyRegistriesAndSomeone(Given[Any, ManyRegistriesAndACaller]):
    """레지스트리 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()
    count: int = 2

    @override
    def describe(self) -> str:
        return f"HuggingFace 레지스트리 {self.count}개와, {_holding(self.role, self.granted)}"

    @override
    async def lay(self, seeding: Any) -> ManyRegistriesAndACaller:
        laid = [
            await seeding.creating(TestSeedHuggingFaceRegistry(name_hint="registry"))
            for _ in range(self.count)
        ]
        caller = await lay_a_caller(seeding, self.role, self.granted)
        return ManyRegistriesAndACaller(
            laid=tuple(seeding.made(one) for one in laid), caller=seeding.made(caller)
        )


def registry_verdicts(
    at: str, node: HuggingFaceRegistryNode, registry: HuggingFaceRegistryData, *, url: str
) -> list[Verdict]:
    """Every place of one registry node, prefixed for a node inside a list."""
    return [
        Held[UUID](f"{at}id", node.id, SameAs(registry.id, "미리 만들어 둔 레지스트리의 id")),
        Held[UUID](
            f"{at}entity_id", node.entity_id, SameAs(registry.id, "미리 만들어 둔 레지스트리의 id")
        ),
        Same(f"{at}name", node.name, registry.name),
        Same(f"{at}url", node.url, url),
        Same(f"{at}token", node.token, registry.token),
    ]


@dataclass(frozen=True)
class Mentions(Condition[str]):
    """이유에 이 말이 들어 있다. 이유의 나머지는 id 를 싣고 있어 실행마다 다르다."""

    phrase: str

    @override
    def says(self) -> str:
        return f"'{self.phrase}'를 담은 이유"

    @override
    def holds(self, got: str) -> bool:
        return self.phrase in got


@dataclass(frozen=True)
class TheRegistryIsEdited(Then[ARegistryAndACaller, HuggingFaceRegistryNode]):
    """미리 만들어 둔 레지스트리가 새 주소를 싣고 통째로 온다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 레지스트리가 새 주소로 온다"

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[HuggingFaceRegistryNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return registry_verdicts("", node, laid.registry, url=EDITED_URL)


@dataclass(frozen=True)
class ThePurgedIdComesBack(Then[ARegistryAndACaller, PurgeHuggingFaceRegistryPayload]):
    """purge 한 레지스트리의 id 가 온다."""

    @override
    def says(self) -> str:
        return "purge 한 레지스트리의 id 가 온다"

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[PurgeHuggingFaceRegistryPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[UUID]("id", payload.id, SameAs(laid.registry.id, "미리 만들어 둔 레지스트리의 id"))
        ]


@dataclass(frozen=True)
class EveryTargetIsEdited(Then[ManyRegistriesAndACaller, Edited]):
    """대상이 모두 새 주소를 싣고 처리된 목록에 오고, 실패 목록은 비어 있다."""

    @override
    def says(self) -> str:
        return "대상 레지스트리가 모두 새 주소로 오고, 실패한 것은 없다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.laid)),
            Same("failed", payload.failed, []),
        ]
        for i, (node, registry) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += registry_verdicts(f"successes[{i}].", node, registry, url=EDITED_URL)
        return verdicts


@dataclass(frozen=True)
class EveryTargetIsPurged(Then[ManyRegistriesAndACaller, Purged]):
    """대상의 id 가 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return "대상 레지스트리의 id 가 모두 처리된 목록에 오고, 실패한 것은 없다"
        return (
            "대상 레지스트리의 id 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 온다"
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (purged, registry) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts.append(
                Held[UUID](
                    f"successes[{i}].id",
                    purged.id,
                    SameAs(registry.id, "미리 만들어 둔 레지스트리의 id"),
                )
            )
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NothingIsProcessed(Then[ManyRegistriesAndACaller, Any]):
    """처리된 레지스트리 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 레지스트리 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, registry) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id", failure.id, SameAs(registry.id, "대상 레지스트리의 id")
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
