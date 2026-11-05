"""What an artifact registry scenario table says besides the call.

A registry is two rows: the per-type row the adapter calls a registry id, and the row
that names it. A table needs the registries a call names and the caller, with the
permission that caller was given on artifact registries in the global scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact_registry.response import ArtifactRegistryGQLNode
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.seeds.artifact_registry.registry import TestSeedHuggingFaceRegistry
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

HUGGINGFACE = ArtifactRegistryType.HUGGINGFACE


def _holding(role: UserRole, granted: tuple[Permission, ...]) -> Says:
    """호출자가 아티팩트 레지스트리에 무엇을 할 수 있는지 한 줄로."""
    who = role.value
    if role is UserRole.SUPERADMIN:
        return Says(f"{who} 한 명", english=f"one {who}")
    if not granted:
        return Says(
            f"아무 권한도 받지 않은 {who} 한 명",
            english=f"one {who} with no permission",
        )
    names = ", ".join(str(permission.name) for permission in granted)
    return Says(
        f"global 에서 아티팩트 레지스트리에 {names} 권한을 받은 {who} 한 명",
        english=f"one {who} granted {names} on artifact registries in global",
    )


@dataclass(frozen=True)
class SomeoneGrantedOnRegistries(TestSeedNest[Laid[UserData]]):
    """그 사용자에게 global 에서 아티팩트 레지스트리에 대한 권한을 준다."""

    domain: Laid[Any]
    granted: tuple[Permission, ...]
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return Says(
            "global 에서 아티팩트 레지스트리 권한을 받은 사용자 준비",
            english="Prepare a user granted permission on artifact registries in global",
        )

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


async def _lay_caller(
    seeding: Any, domain: Laid[Any], role: UserRole, granted: tuple[Permission, ...]
) -> Laid[UserData]:
    """The caller a row asks for, with the permissions the row names."""
    if not granted:
        return await seeding.within(SomeoneOf(domain, role=role))
    return await seeding.within(SomeoneGrantedOnRegistries(domain, granted, role=role))


@dataclass(frozen=True)
class ARegistryAndACaller:
    """레지스트리 하나와, 그것을 부를 사람."""

    registry: HuggingFaceRegistryData
    caller: UserData


@dataclass(frozen=True)
class ManyRegistriesAndACaller:
    """레지스트리 여럿과, 그것들을 부를 사람."""

    laid: tuple[HuggingFaceRegistryData, ...]
    caller: UserData


@dataclass(frozen=True)
class ARegistryAndSomeone(Given[Any, ARegistryAndACaller]):
    """레지스트리 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        holding = _holding(self.role, self.granted)
        return Says(
            f"HuggingFace 레지스트리 하나와, {holding}",
            english=f"one HuggingFace registry and {holding.english}",
        )

    @override
    async def lay(self, seeding: Any) -> ARegistryAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        registry = await seeding.creating(TestSeedHuggingFaceRegistry(name_hint="registry"))
        caller = await _lay_caller(seeding, domain, self.role, self.granted)
        return ARegistryAndACaller(seeding.made(registry), seeding.made(caller))


@dataclass(frozen=True)
class ManyRegistriesAndSomeone(Given[Any, ManyRegistriesAndACaller]):
    """레지스트리 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()
    count: int = 2

    @override
    def describe(self) -> str:
        holding = _holding(self.role, self.granted)
        return Says(
            f"HuggingFace 레지스트리 {self.count}개와, {holding}",
            english=f"{self.count} HuggingFace registries and {holding.english}",
        )

    @override
    async def lay(self, seeding: Any) -> ManyRegistriesAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        laid = [
            await seeding.creating(TestSeedHuggingFaceRegistry(name_hint="registry"))
            for _ in range(self.count)
        ]
        caller = await _lay_caller(seeding, domain, self.role, self.granted)
        return ManyRegistriesAndACaller(
            laid=tuple(seeding.made(one) for one in laid), caller=seeding.made(caller)
        )


def registry_verdicts(
    prefix: str, node: ArtifactRegistryGQLNode, registry: HuggingFaceRegistryData
) -> list[Verdict]:
    """Every place of one registry node, prefixed for a node inside a list."""
    return [
        Held[UUID](
            f"{prefix}id",
            node.id,
            SameAs(
                node.entity_id,
                Says(
                    "같은 응답의 entity id",
                    english="the entity id in the same answer",
                ),
            ),
        ),
        Held[UUID](
            f"{prefix}entity_id",
            node.entity_id,
            SameAs(
                node.id,
                Says(
                    "같은 응답의 id",
                    english="the id in the same answer",
                ),
            ),
        ),
        Held[UUID](
            f"{prefix}registry_id",
            node.registry_id,
            SameAs(
                registry.id,
                Says(
                    "미리 저장한 레지스트리의 id",
                    english="the id of the registry made in advance",
                ),
            ),
        ),
        Same(f"{prefix}name", node.name, registry.name),
        Same(f"{prefix}type", node.type, HUGGINGFACE),
    ]


@dataclass(frozen=True)
class TheRegistryNode(Then[ARegistryAndACaller, ArtifactRegistryGQLNode]):
    """레지스트리 노드 하나가 통째로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 레지스트리 전체가 옵니다",
            english="the whole registry made in advance comes back",
        )

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[ArtifactRegistryGQLNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Same("registry", node, None)]
        return registry_verdicts("", node, laid.registry)
