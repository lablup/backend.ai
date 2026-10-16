"""What an object storage scenario table says besides the call.

An object storage is created in global alone and reached afterwards by id. A table needs
the caller and the object storage or object storages the call names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.object_storage.response import (
    ObjectStorageNode,
    PurgeObjectStoragePayload,
)
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
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
from bai_scenario.components.domain import Mentions
from bai_scenario.components.system import KEPT, Kept, lay_a_caller, role_named
from bai_scenario.seeds.object_storage.object_storage import TestSeedObjectStorage


@dataclass(frozen=True)
class AStorageAndACaller:
    """object storage 하나와, 그것을 호출할 사용자."""

    storage: ObjectStorageData
    caller: UserData


@dataclass(frozen=True)
class ManyStoragesAndACaller:
    """object storage 여럿과, 그것들을 한 번에 호출할 사용자."""

    laid: tuple[ObjectStorageData, ...]
    caller: UserData


@dataclass(frozen=True)
class AStorageAndSomeone(Given[Any, AStorageAndACaller]):
    """object storage 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"object storage 하나와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> AStorageAndACaller:
        storage = await seeding.creating(TestSeedObjectStorage())
        caller = await lay_a_caller(seeding, self.role)
        return AStorageAndACaller(seeding.made(storage), seeding.made(caller))


@dataclass(frozen=True)
class ManyStoragesAndSomeone(Given[Any, ManyStoragesAndACaller]):
    """object storage 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return f"object storage {self.count}개와, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyStoragesAndACaller:
        storages = [await seeding.creating(TestSeedObjectStorage()) for _ in range(self.count)]
        caller = await lay_a_caller(seeding, self.role)
        return ManyStoragesAndACaller(
            laid=tuple(seeding.made(one) for one in storages),
            caller=seeding.made(caller),
        )


def storage_verdicts(
    at: str, node: ObjectStorageNode, storage: ObjectStorageData, host: str | Kept
) -> list[Verdict]:
    """Every place of one object storage node, prefixed for a node inside a list."""
    return [
        Held[UUID](f"{at}id", node.id, SameAs[UUID](storage.id, "미리 만들어 둔 object storage")),
        Held[UUID](
            f"{at}entity_id",
            node.entity_id,
            SameAs[UUID](storage.id, "미리 만들어 둔 object storage"),
        ),
        Same(f"{at}name", node.name, storage.name),
        Same(f"{at}host", node.host, storage.host if isinstance(host, Kept) else host),
        Same(f"{at}access_key", node.access_key, storage.access_key),
        Same(f"{at}secret_key", node.secret_key, storage.secret_key),
        Same(f"{at}endpoint", node.endpoint, storage.endpoint),
        Same(f"{at}region", node.region, storage.region),
    ]


@dataclass(frozen=True)
class TheStorageNode(Then[AStorageAndACaller, ObjectStorageNode]):
    """미리 만들어 둔 object storage 가 통째로 반환된다. 수정 요청은 바뀌어야 하는 필드만 인자로 준다."""

    host: str | Kept = KEPT

    @override
    def says(self) -> str:
        return "미리 만들어 둔 object storage 전체가 반환된다"

    @override
    def look(
        self, laid: AStorageAndACaller, answered: Answered[ObjectStorageNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return storage_verdicts("", node, laid.storage, self.host)


@dataclass(frozen=True)
class ThePurgedStorageId(Then[AStorageAndACaller, PurgeObjectStoragePayload]):
    """purge 한 object storage 의 id 를 담은 응답."""

    @override
    def says(self) -> str:
        return "purge 한 object storage 의 id 가 반환된다"

    @override
    def look(
        self, laid: AStorageAndACaller, answered: Answered[PurgeObjectStoragePayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID](
                "id", payload.id, SameAs[UUID](laid.storage.id, "미리 만들어 둔 object storage")
            )
        ]


@dataclass(frozen=True)
class EveryStorageIsProcessed(Then[ManyStoragesAndACaller, PartialBulkPayload[ObjectStorageNode]]):
    """대상이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    host: str | Kept = KEPT
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return "대상 object storage 가 모두 처리된 목록에 오고, 실패한 것은 없다"
        return (
            "대상 object storage 가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 온다"
        )

    @override
    def look(
        self,
        laid: ManyStoragesAndACaller,
        answered: Answered[PartialBulkPayload[ObjectStorageNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, storage) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += storage_verdicts(f"successes[{i}].", node, storage, self.host)
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
class NothingIsProcessed(Then[ManyStoragesAndACaller, PartialBulkPayload[ObjectStorageNode]]):
    """처리된 object storage 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 object storage 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: ManyStoragesAndACaller,
        answered: Answered[PartialBulkPayload[ObjectStorageNode]],
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
                    f"failed[{i}].id", failure.id, SameAs(storage.id, "대상 object storage 의 id")
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
