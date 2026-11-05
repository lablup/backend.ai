"""object storage 하나 조회와 여러 id 조회."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.object_storage.response import ObjectStorageNode
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
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
from bai_scenario.components.object_storage import (
    AStorageAndACaller,
    AStorageAndSomeone,
    ManyStoragesAndACaller,
    ManyStoragesAndSomeone,
    TheStorageNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING_ID = uuid4()

type Loaded = list[ObjectStorageNode | Exception | None]
type ReadingStep = Scenario[TestSeedingSession, Any, ObjectStorageAdapter, Any]


@dataclass(frozen=True)
class Getting(When[AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]):
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
    async def call(
        self, adapter: ObjectStorageAdapter, laid: AStorageAndACaller
    ) -> ObjectStorageNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.storage.id)


@dataclass(frozen=True)
class ReadingMany(When[ManyStoragesAndACaller, ObjectStorageAdapter, Loaded]):
    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyStoragesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 object storage 둘과 존재하지 않는 id 하나를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} loads two object storages seeded in advance and one id "
                "that does not exist at once"
            ),
        )

    def ids(self, laid: ManyStoragesAndACaller) -> list[ObjectStorageID]:
        return [
            ObjectStorageID(laid.laid[0].id),
            ObjectStorageID(MISSING_ID),
            ObjectStorageID(laid.laid[1].id),
        ]

    @override
    async def call(self, adapter: ObjectStorageAdapter, laid: ManyStoragesAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self.ids(laid))


@dataclass(frozen=True)
class TheOrderIsKept(Then[ManyStoragesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 object storage 는 요청한 순서대로 반환되고, 존재하지 않는 id 의 항목은 "
            "비어 있습니다",
            english=(
                "the object storages seeded in advance come back in the requested order, and the "
                "entry for the id that does not exist is empty"
            ),
        )

    @override
    def look(self, laid: ManyStoragesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [MissingResponse(answered.raised)]
        if len(got) != 3:
            return [Same("length", len(got), 3)]
        first, middle, last = got
        return [
            Same("length", len(got), 3),
            Same(
                "[0].name",
                first.name if isinstance(first, ObjectStorageNode) else None,
                laid.laid[0].name,
            ),
            Same("[1]", middle, None),
            Same(
                "[2].name",
                last.name if isinstance(last, ObjectStorageNode) else None,
                laid.laid[1].name,
            ),
        ]


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
            Same("length", len(got), 3),
            *[
                Refused(NotEnoughPermission, one if isinstance(one, Exception) else None)
                for one in got
            ],
        ]


@dataclass(frozen=True)
class TheSuperadminGetsAStorage(
    Scenario[TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-gets-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 object storage 하나를 조회하면 미리 저장한 object storage 전체가 "
            "반환됩니다",
            english=(
                "when the superadmin reads one object storage, the whole seeded object storage "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]:
        return Getting()

    @override
    def then(self) -> Then[AStorageAndACaller, ObjectStorageNode]:
        return TheStorageNode()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotGet(
    Scenario[TestSeedingSession, AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-get-an-object-storage"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 object storage 하나를 조회하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing reads one object storage, it is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AStorageAndACaller]:
        return AStorageAndSomeone()

    @override
    def when(self) -> When[AStorageAndACaller, ObjectStorageAdapter, ObjectStorageNode]:
        return Getting()

    @override
    def then(self) -> Then[AStorageAndACaller, ObjectStorageNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadsManyInOrder(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-several-object-storages-in-the-requested-order"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 object storage 둘과 존재하지 않는 id 하나를 한 번에 "
            "조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 비어 있습니다",
            english=(
                "when the superadmin loads two object storages seeded in advance and one id that "
                "does not exist at once, the two come back in the requested order and the entry "
                "for the id that does not exist is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Loaded]:
        return TheOrderIsKept()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedOnEveryId(
    Scenario[TestSeedingSession, ManyStoragesAndACaller, ObjectStorageAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-many-object-storage-ids-is-refused-on-every-id"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 object storage id 여럿을 한 번에 조회하면, 요청 전체가 "
            "거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다",
            english=(
                "when a user granted nothing loads several object storage ids at once, instead "
                "of rejecting the whole request, every entry comes back holding a rejection for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyStoragesAndACaller]:
        return ManyStoragesAndSomeone()

    @override
    def when(self) -> When[ManyStoragesAndACaller, ObjectStorageAdapter, Loaded]:
        return ReadingMany()

    @override
    def then(self) -> Then[ManyStoragesAndACaller, Loaded]:
        return EveryIdIsRefused()


SCENARIOS: list[ReadingStep] = [
    TheSuperadminGetsAStorage(),
    AUserGrantedNothingMayNotGet(),
    TheSuperadminReadsManyInOrder(),
    AUserGrantedNothingIsRefusedOnEveryId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep,
    adapter: ObjectStorageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
