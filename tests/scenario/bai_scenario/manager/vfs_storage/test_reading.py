"""VFS storage 하나 조회와 여러 id 조회."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.common.dto.manager.v2.vfs_storage.response import VFSStorageNode
from ai.backend.manager.api.adapters.vfs_storage.adapter import VFSStorageAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.system import KEPT
from bai_scenario.components.vfs_storage import (
    AStorageAndACaller,
    AStorageAndSomeone,
    ManyStoragesAndACaller,
    ManyStoragesAndSomeone,
    TheStorageNode,
    storage_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Node = VFSStorageNode
type Loaded = list[VFSStorageNode | Exception | None]
type ReadingStep = Scenario[TestSeedingSession, Any, VFSStorageAdapter, Any]


@dataclass(frozen=True)
class Getting(When[AStorageAndACaller, VFSStorageAdapter, Node]):
    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AStorageAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.storage.name}을 조회합니다",
            english=f"{laid.caller.username} reads {laid.storage.name}",
        )

    @override
    async def call(self, adapter: VFSStorageAdapter, laid: AStorageAndACaller) -> Node:
        with ActingAs(laid.caller):
            return await adapter.get(laid.storage.id)


@dataclass(frozen=True)
class ReadingMany(When[ManyStoragesAndACaller, VFSStorageAdapter, Loaded]):
    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 VFS storage 둘을 한 번에 조회합니다",
            english=f"{laid.caller.username} loads two VFS storages seeded in advance at once",
        )

    def ids(self, laid: ManyStoragesAndACaller) -> list[VFSStorageID]:
        return [
            VFSStorageID(laid.laid[0].id),
            VFSStorageID(laid.laid[1].id),
        ]

    @override
    async def call(self, adapter: VFSStorageAdapter, laid: ManyStoragesAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self.ids(laid))


@dataclass(frozen=True)
class TheOrderIsKept(Then[ManyStoragesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 VFS storage 는 요청한 순서대로 반환됩니다",
            english="the VFS storages seeded in advance come back in the requested order",
        )

    @override
    def look(self, laid: ManyStoragesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        if len(got) != len(laid.laid):
            return [Same("length", len(got), len(laid.laid))]
        verdicts: list[Verdict] = [Same("length", len(got), len(laid.laid))]
        for i, (one, storage) in enumerate(zip(got, laid.laid, strict=True)):
            if not isinstance(one, VFSStorageNode):
                verdicts.append(Same(f"[{i}]", type(one).__name__, VFSStorageNode.__name__))
                continue
            verdicts += storage_verdicts(f"[{i}].", one, storage, KEPT)
        return verdicts


@dataclass(frozen=True)
class EveryIdIsRefused(Then[ManyStoragesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "항목마다 권한 부족 거부가 담겨 반환됩니다",
            english="every entry comes back holding a rejection for lack of permission",
        )

    @override
    def look(self, laid: ManyStoragesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
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


@dataclass(frozen=True)
class AUserGrantedReadGetsAStorage(
    Scenario[TestSeedingSession, AStorageAndACaller, VFSStorageAdapter, Node]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-gets-a-vfs-storage"

    @override
    def describe(self) -> str:
        return Says(
            "VFS storage 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 VFS storage 전체가 "
            "반환됩니다",
            english=(
                "when a user granted permission to read VFS storages reads one, the whole seeded "
                "VFS storage comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[AStorageAndACaller, VFSStorageAdapter, Node]:
        return Getting()

    @override
    def then(self) -> Then[AStorageAndACaller, Node]:
        return TheStorageNode()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotGet(
    Scenario[TestSeedingSession, AStorageAndACaller, VFSStorageAdapter, Node]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-get-a-vfs-storage"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 VFS storage 하나를 조회하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing reads one VFS storage, it is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone()

    @override
    def when(self) -> When[AStorageAndACaller, VFSStorageAdapter, Node]:
        return Getting()

    @override
    def then(self) -> Then[AStorageAndACaller, Node]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedReadReadsManyInOrder(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-several-vfs-storages-in-the-requested-order"

    @override
    def describe(self) -> str:
        return Says(
            "VFS storage 조회 권한을 받은 사용자가 미리 저장한 VFS storage 둘을 한 번에 조회하면, "
            "둘은 요청한 순서대로 반환됩니다",
            english=(
                "when a user granted permission to read VFS storages loads two VFS storages seeded "
                "in advance at once, the two come back in the requested order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Loaded]:
        return TheOrderIsKept()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedOnEveryId(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, VFSStorageAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-many-vfs-storage-ids-is-refused-on-every-id"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 VFS storage id 여럿을 한 번에 조회하면, 요청 전체가 "
            "거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다",
            english=(
                "when a user granted nothing loads several VFS storage ids at once, instead of "
                "rejecting the whole request, every entry comes back holding a rejection for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(self) -> When[ManyStoragesAndACaller, VFSStorageAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Loaded]:
        return EveryIdIsRefused()


SCENARIOS: list[ReadingStep] = [
    AUserGrantedReadGetsAStorage(),
    AUserGrantedNothingMayNotGet(),
    AUserGrantedReadReadsManyInOrder(),
    AUserGrantedNothingIsRefusedOnEveryId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep,
    adapter: VFSStorageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
