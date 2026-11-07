"""What a VFS storage scenario table says besides the call.

An VFS storage is created in global alone and reached afterwards by id. A table needs
the caller and the VFS storage or VFS storages the call names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfs_storage import VFSStorageEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    PurgeVFSStoragePayload,
    VFSStorageNode,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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
from bai_scenario.components.answers import TheFailedItemIsRefused
from bai_scenario.components.domain import WAS_HERE, Mentions, SomeoneOf
from bai_scenario.components.system import KEPT, Kept, role_named
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.vfs_storage.vfs_storage import TestSeedVFSStorage


def _holding(role: UserRole, granted: tuple[Permission, ...]) -> Says:
    if granted:
        names = ", ".join(str(one.name) for one in granted)
        return Says(
            f"VFS storage 에 {names} 권한을 받은 사용자 한 명",
            english=f"one user granted {names} on VFS storages",
        )
    who = role_named(role)
    return Says(f"{who} 한 명", english=f"one {in_language(who, Language.ENGLISH)}")


@dataclass(frozen=True)
class SomeoneGrantedOnStorages(TestSeedNest[Laid[UserData]]):
    """그 사용자에게 global 에서 VFS storage 권한을 준다."""

    domain: Laid[Any]
    granted: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        names = ", ".join(str(one.name) for one in self.granted)
        return Says(
            f"global 에서 VFS storage 에 {names} 권한을 받은 사용자 준비",
            english=f"Prepare a user granted {names} on VFS storages in global",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.GLOBAL), name_hint="storage-keeper"
            ),
            someone,
        )
        for one in self.granted:
            seed.adding(
                TestSeedPermission(entity_type=VFSStorageEntityType(), permission=one), role
            )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def lay_a_granted_caller(
    seeding: Any, role: UserRole = UserRole.USER, granted: tuple[Permission, ...] = ()
) -> Laid[UserData]:
    """A user of the given role, granted the given permissions on VFS storages."""
    home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
    if not granted:
        plain: Laid[UserData] = await seeding.within(SomeoneOf(home, role=role))
        return plain
    granted_caller: Laid[UserData] = await seeding.within(SomeoneGrantedOnStorages(home, granted))
    return granted_caller


@dataclass(frozen=True)
class AStorageAndACaller:
    """VFS storage 하나와, 그것을 호출할 사용자."""

    storage: VFSStorageData
    caller: UserData


@dataclass(frozen=True)
class ManyStoragesAndACaller:
    """VFS storage 여럿과, 그것들을 한 번에 호출할 사용자."""

    laid: tuple[VFSStorageData, ...]
    caller: UserData


@dataclass(frozen=True)
class AStorageAndSomeone(Given[Any, AStorageAndACaller]):
    """VFS storage 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"VFS storage 하나와, {who}",
            english=f"one VFS storage and {in_language(who, Language.ENGLISH)}",
        )

    @override
    async def lay(self, seeding: Any) -> AStorageAndACaller:
        storage = await seeding.creating(TestSeedVFSStorage())
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return AStorageAndACaller(seeding.made(storage), seeding.made(caller))


@dataclass(frozen=True)
class ManyStoragesAndSomeone(Given[Any, ManyStoragesAndACaller]):
    """VFS storage 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()
    count: int = 2

    @override
    def describe(self) -> str:
        who = _holding(self.role, self.granted)
        return Says(
            f"VFS storage {self.count}개와, {who}",
            english=f"{self.count} VFS storages and {in_language(who, Language.ENGLISH)}",
        )

    @override
    async def lay(self, seeding: Any) -> ManyStoragesAndACaller:
        storages = [await seeding.creating(TestSeedVFSStorage()) for _ in range(self.count)]
        caller = await lay_a_granted_caller(seeding, self.role, self.granted)
        return ManyStoragesAndACaller(
            laid=tuple(seeding.made(one) for one in storages),
            caller=seeding.made(caller),
        )


def storage_verdicts(
    at: str, node: VFSStorageNode, storage: VFSStorageData, base_path: str | Kept
) -> list[Verdict]:
    """Every place of one VFS storage node, prefixed for a node inside a list."""
    return [
        Held[UUID](
            f"{at}id",
            node.id,
            SameAs[UUID](
                storage.id,
                Says("미리 저장한 VFS storage", english="the VFS storage seeded in advance"),
            ),
        ),
        Held[UUID](
            f"{at}entity_id",
            node.entity_id,
            SameAs[UUID](
                storage.id,
                Says("미리 저장한 VFS storage", english="the VFS storage seeded in advance"),
            ),
        ),
        Same(f"{at}name", node.name, storage.name),
        Same(f"{at}host", node.host, storage.host),
        Same(
            f"{at}base_path",
            node.base_path,
            str(storage.base_path) if isinstance(base_path, Kept) else base_path,
        ),
    ]


@dataclass(frozen=True)
class TheStorageNode(Then[AStorageAndACaller, VFSStorageNode]):
    """미리 만들어 둔 VFS storage 가 통째로 반환된다. 수정 요청은 바뀌어야 하는 필드만 인자로 준다."""

    base_path: str | Kept = KEPT

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 VFS storage 전체가 반환됩니다",
            english="the whole VFS storage seeded in advance comes back",
        )

    @override
    def look(self, laid: AStorageAndACaller, answered: Answered[VFSStorageNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return storage_verdicts("", node, laid.storage, self.base_path)


@dataclass(frozen=True)
class ThePurgedStorageId(Then[AStorageAndACaller, PurgeVFSStoragePayload]):
    """purge 한 VFS storage 의 id 를 담은 응답."""

    @override
    def says(self) -> str:
        return Says(
            "purge 한 VFS storage 의 id 가 반환됩니다",
            english="the id of the purged VFS storage comes back",
        )

    @override
    def look(
        self, laid: AStorageAndACaller, answered: Answered[PurgeVFSStoragePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs[UUID](
                    laid.storage.id,
                    Says(
                        "미리 저장한 VFS storage",
                        english="the VFS storage seeded in advance",
                    ),
                ),
            ),
            Held[UUID](
                "entity_id",
                payload.entity_id,
                SameAs[UUID](
                    laid.storage.id,
                    Says(
                        "미리 저장한 VFS storage",
                        english="the VFS storage seeded in advance",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class EveryStorageIsProcessed(Then[ManyStoragesAndACaller, PartialBulkPayload[VFSStorageNode]]):
    """대상이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    base_path: str | Kept = KEPT
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return Says(
                "대상 VFS storage 가 모두 처리된 목록에 오고, 실패한 것은 없습니다",
                english="every target VFS storage comes back in the processed list, "
                "and nothing failed",
            )
        return Says(
            "대상 VFS storage 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 옵니다",
            english="every target VFS storage comes back in the processed list, and an "
            "unknown id comes back in the failed list because no target answers to it",
        )

    @override
    def look(
        self,
        laid: ManyStoragesAndACaller,
        answered: Answered[PartialBulkPayload[VFSStorageNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, storage) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += storage_verdicts(f"successes[{i}].", node, storage, self.base_path)
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NothingIsProcessed(Then[ManyStoragesAndACaller, PartialBulkPayload[VFSStorageNode]]):
    """처리된 VFS storage 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 VFS storage 없이 대상이 모두 실패 목록에 옵니다",
            english=("no VFS storage is processed and every target comes back in the failed list"),
        )

    @override
    def look(
        self,
        laid: ManyStoragesAndACaller,
        answered: Answered[PartialBulkPayload[VFSStorageNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, storage) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        storage.id,
                        Says(
                            "대상 VFS storage 의 id",
                            english="the id of the target VFS storage",
                        ),
                    ),
                ),
                TheFailedItemIsRefused(f"failed[{i}]", failure.message, self.reason),
            ]
        return verdicts
