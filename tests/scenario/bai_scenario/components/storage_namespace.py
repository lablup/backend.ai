"""What a storage namespace scenario table says besides the call.

A namespace is registered under an object storage and reached afterwards by the pair
of that storage and its name. A table needs the caller and the rows the call names.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.storage_namespace.response import (
    StorageNamespaceNode,
    UnregisterStorageNamespacePayload,
)
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.system import role_named
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.object_storage.object_storage import TestSeedObjectStorage
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.storage_namespace.storage_namespace import (
    SEEDED_NAMESPACE,
    TestSeedStorageNamespace,
)


def _holding(role: UserRole, granted: tuple[Permission, ...]) -> Says:
    if granted:
        names = ", ".join(str(one.name) for one in granted)
        return Says(
            f"저장소 네임스페이스에 {names} 권한을 받은 사용자 한 명",
            english=f"one user granted {names} on storage namespaces",
        )
    who = role_named(role)
    return Says(f"{who} 한 명", english=f"one {in_language(who, Language.ENGLISH)}")


@dataclass(frozen=True)
class SomeoneGrantedOnNamespaces(TestSeedNest[Laid[UserData]]):
    """그 사용자에게 global 에서 저장소 네임스페이스 권한을 준다."""

    domain: Laid[Any]
    granted: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        names = ", ".join(str(one.name) for one in self.granted)
        return Says(
            f"global 에서 저장소 네임스페이스에 {names} 권한을 받은 사용자 준비",
            english=f"Prepare a user granted {names} on storage namespaces in global",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.GLOBAL), name_hint="namespace-keeper"
            ),
            someone,
        )
        for one in self.granted:
            seed.adding(
                TestSeedPermission(entity_type=StorageNamespaceEntityType(), permission=one), role
            )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def lay_a_granted_caller(
    seeding: Any, role: UserRole = UserRole.USER, granted: tuple[Permission, ...] = ()
) -> Laid[UserData]:
    """A user of the given role, granted the given permissions on storage namespaces."""
    home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
    if not granted:
        plain: Laid[UserData] = await seeding.within(SomeoneOf(home, role=role))
        return plain
    granted_caller: Laid[UserData] = await seeding.within(SomeoneGrantedOnNamespaces(home, granted))
    return granted_caller


@dataclass(frozen=True)
class AStorageAndACaller:
    """object storage 하나와, 그것에 네임스페이스를 등록할 사용자."""

    storage: ObjectStorageData
    caller: UserData


@dataclass(frozen=True)
class ANamespaceAndACaller:
    """등록된 네임스페이스 하나와, 그것을 부를 사용자."""

    namespace: StorageNamespaceData
    storage: ObjectStorageData
    caller: UserData


@dataclass(frozen=True)
class ManyNamespacesAndACaller:
    """등록된 네임스페이스 둘과, 그것들을 한 번에 부를 사용자."""

    laid: tuple[StorageNamespaceData, ...]
    storage: ObjectStorageData
    caller: UserData


def lay_namespaces(
    seed: TestSeeder, storage: Laid[ObjectStorageData]
) -> list[Laid[StorageNamespaceData]]:
    """Two namespaces on one storage, the premise of every list and search row."""
    return [
        seed.creating_from(TestSeedStorageNamespace(namespace=SEEDED_NAMESPACE), storage),
        seed.creating_from(TestSeedStorageNamespace(namespace="second-bucket"), storage),
    ]


@dataclass(frozen=True)
class AStorageAndSomeone(Given[Any, AStorageAndACaller]):
    """object storage 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"object storage 하나와, {who}",
            english=f"one object storage and {in_language(who, Language.ENGLISH)}",
        )

    @override
    async def lay(self, seeding: Any) -> AStorageAndACaller:
        storage = await seeding.creating(TestSeedObjectStorage())
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return AStorageAndACaller(seeding.made(storage), seeding.made(caller))


@dataclass(frozen=True)
class ANamespaceAndSomeone(Given[Any, ANamespaceAndACaller]):
    """한 object storage 아래 등록된 네임스페이스 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"object storage 하나와 그 아래 등록된 네임스페이스 하나, {who}",
            english=(
                "one object storage with one namespace registered on it and "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ANamespaceAndACaller:
        storage = await seeding.creating(TestSeedObjectStorage())
        namespace = await seeding.creating_from(TestSeedStorageNamespace(), storage)
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return ANamespaceAndACaller(
            seeding.made(namespace), seeding.made(storage), seeding.made(caller)
        )


@dataclass(frozen=True)
class ManyNamespacesOnAStorage(TestSeedNest[list[Laid[StorageNamespaceData]]]):
    """한 object storage 아래 네임스페이스 둘."""

    storage: Laid[ObjectStorageData]

    @override
    def kind(self) -> str:
        return Says(
            "네임스페이스 둘을 등록한 object storage 준비",
            english="Prepare an object storage with two namespaces registered",
        )

    @override
    def lay(self, seed: TestSeeder) -> list[Laid[StorageNamespaceData]]:
        return lay_namespaces(seed, self.storage)


@dataclass(frozen=True)
class ManyNamespacesAndSomeone(Given[Any, ManyNamespacesAndACaller]):
    """object storage 하나와 그 아래 네임스페이스 둘, 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"object storage 하나와 그 아래 등록된 네임스페이스 둘, {who}",
            english=(
                "one object storage with two namespaces registered on it and "
                f"{in_language(who, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyNamespacesAndACaller:
        storage = await seeding.creating(TestSeedObjectStorage())
        namespaces = await seeding.within(ManyNamespacesOnAStorage(storage))
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return ManyNamespacesAndACaller(
            laid=tuple(seeding.made(one) for one in namespaces),
            storage=seeding.made(storage),
            caller=seeding.made(caller),
        )


def namespace_verdicts(
    at: str, node: StorageNamespaceNode, namespace: StorageNamespaceData
) -> list[Verdict]:
    """Every place of one namespace node, prefixed for a node inside a list."""
    seeded = Says("미리 저장한 네임스페이스", english="the namespace seeded in advance")
    return [
        Held[UUID](f"{at}id", node.id, SameAs[UUID](namespace.id, seeded)),
        Held[UUID](f"{at}entity_id", node.entity_id, SameAs[UUID](namespace.id, seeded)),
        Held[UUID](
            f"{at}storage_id",
            node.storage_id,
            SameAs[UUID](
                namespace.storage_id,
                Says(
                    "그 네임스페이스가 등록된 object storage 의 id",
                    english="the id of the object storage it is registered on",
                ),
            ),
        ),
        Same(f"{at}namespace", node.namespace, namespace.namespace),
    ]


@dataclass(frozen=True)
class TheNamespaceNode(Then[ANamespaceAndACaller, StorageNamespaceNode]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 네임스페이스 전체가 반환됩니다",
            english="the whole namespace seeded in advance comes back",
        )

    @override
    def look(
        self, laid: ANamespaceAndACaller, answered: Answered[StorageNamespaceNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return namespace_verdicts("", node, laid.namespace)


@dataclass(frozen=True)
class TheUnregisteredStorageId(Then[ANamespaceAndACaller, UnregisterStorageNamespacePayload]):
    @override
    def says(self) -> str:
        return Says(
            "네임스페이스를 빼낸 object storage 의 id 가 반환됩니다",
            english="the id of the object storage the namespace left comes back",
        )

    @override
    def look(
        self, laid: ANamespaceAndACaller, answered: Answered[UnregisterStorageNamespacePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs[UUID](
                    laid.storage.id,
                    Says(
                        "미리 저장한 object storage",
                        english="the object storage seeded in advance",
                    ),
                ),
            )
        ]


def the_namespaces(
    got: Sequence[StorageNamespaceNode], laid: ManyNamespacesAndACaller
) -> list[Verdict]:
    """The seeded namespaces, each checked whole. The call fixes no order, so ids pair them."""
    if len(got) != len(laid.laid):
        return [Same("length", len(got), len(laid.laid))]
    verdicts: list[Verdict] = [Same("length", len(got), len(laid.laid))]
    ordered_nodes = sorted(got, key=lambda one: one.id.int)
    ordered_rows = sorted(laid.laid, key=lambda one: one.id.int)
    for i, (node, namespace) in enumerate(zip(ordered_nodes, ordered_rows, strict=True)):
        verdicts += namespace_verdicts(f"[{i}].", node, namespace)
    return verdicts


@dataclass(frozen=True)
class TheNamespacesAreListed(Then[ManyNamespacesAndACaller, list[StorageNamespaceNode]]):
    @override
    def says(self) -> str:
        return Says(
            "그 object storage 에 등록된 네임스페이스가 모두 반환됩니다",
            english="every namespace registered on the object storage comes back",
        )

    @override
    def look(
        self, laid: ManyNamespacesAndACaller, answered: Answered[list[StorageNamespaceNode]]
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        return the_namespaces(items, laid)


type Loaded = list[StorageNamespaceNode | Exception | None]


def loaded_verdicts(
    got: Sequence[StorageNamespaceNode | Exception | None],
    laid: ManyNamespacesAndACaller,
) -> list[Verdict]:
    """The seeded namespaces in the requested order, each checked whole."""
    verdicts: list[Verdict] = [Same("length", len(got), len(laid.laid))]
    for i, (one, namespace) in enumerate(zip(got, laid.laid, strict=True)):
        if not isinstance(one, StorageNamespaceNode):
            verdicts.append(Same(f"[{i}]", type(one).__name__, StorageNamespaceNode.__name__))
            continue
        verdicts += namespace_verdicts(f"[{i}].", one, namespace)
    return verdicts


@dataclass(frozen=True)
class TheOrderIsKept(Then[ManyNamespacesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 네임스페이스는 요청한 순서대로 반환됩니다",
            english="the namespaces seeded in advance come back in the requested order",
        )

    @override
    def look(self, laid: ManyNamespacesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        if len(got) != len(laid.laid):
            return [Same("length", len(got), len(laid.laid))]
        return loaded_verdicts(got, laid)


@dataclass(frozen=True)
class EveryIdIsRefused(Then[ManyNamespacesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "항목마다 권한 부족 거부가 담겨 반환됩니다",
            english="every entry comes back holding a rejection for lack of permission",
        )

    @override
    def look(self, laid: ManyNamespacesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(got), len(laid.laid)),
            *[
                Refused(NotEnoughPermission, one if isinstance(one, Exception) else None)
                for one in got
            ],
        ]
