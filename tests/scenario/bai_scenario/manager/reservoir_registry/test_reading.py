"""Reservoir 레지스트리 하나 조회, 여러 id 조회와 일괄 조회."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    ReservoirRegistryNode,
)
from ai.backend.manager.api.adapters.reservoir_registry.adapter import (
    ReservoirRegistryAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.reservoir_registry import (
    ARegistryAndACaller,
    ARegistryAndSomeone,
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
    registry_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING_ID = uuid4()

type Loaded = list[ReservoirRegistryNode | Exception | None]
type ReadingStep = Scenario[TestSeedingSession, Any, ReservoirRegistryAdapter, Any]


def registry_snapshot(node: ReservoirRegistryNode) -> tuple[Any, ...]:
    return (
        node.id,
        node.entity_id,
        node.name,
        node.endpoint,
        node.access_key,
        node.secret_key,
        node.api_version,
    )


@dataclass(frozen=True)
class Getting(When[ARegistryAndACaller, ReservoirRegistryAdapter, ReservoirRegistryNode]):
    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.registry.name}을 조회합니다",
            english=f"{laid.caller.username} reads {laid.registry.name}",
        )

    @override
    async def call(
        self, adapter: ReservoirRegistryAdapter, laid: ARegistryAndACaller
    ) -> ReservoirRegistryNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.registry.id)


@dataclass(frozen=True)
class ReadingMany(
    When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, list[ReservoirRegistryNode]]
):
    @override
    def operation(self) -> str:
        return "get_many"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 레지스트리 둘을 id 로 한 번에 조회합니다",
            english=f"{laid.caller.username} reads two registries seeded in advance by id at once",
        )

    @override
    async def call(
        self, adapter: ReservoirRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> list[ReservoirRegistryNode]:
        with ActingAs(laid.caller):
            return await adapter.get_many([one.id for one in laid.laid])


@dataclass(frozen=True)
class LoadingByIds(When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Loaded]):
    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 레지스트리 둘과 존재하지 않는 id 하나를 한 "
            "번에 조회합니다",
            english=(
                f"{laid.caller.username} loads two registries seeded in advance and one id that "
                "does not exist at once"
            ),
        )

    def ids(self, laid: ManyRegistriesAndACaller) -> list[ArtifactRegistryID]:
        return [
            ArtifactRegistryID(laid.laid[0].id),
            ArtifactRegistryID(MISSING_ID),
            ArtifactRegistryID(laid.laid[1].id),
        ]

    @override
    async def call(
        self, adapter: ReservoirRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self.ids(laid))


@dataclass(frozen=True)
class TheRegistryNode(Then[ARegistryAndACaller, ReservoirRegistryNode]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 레지스트리 전체가 반환됩니다",
            english="the whole registry seeded in advance comes back",
        )

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[ReservoirRegistryNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return registry_verdicts("", node, laid.registry, endpoint=laid.registry.endpoint)


@dataclass(frozen=True)
class TheRegistriesAreReturned(Then[ManyRegistriesAndACaller, list[ReservoirRegistryNode]]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 레지스트리가 모두 반환됩니다",
            english="every registry seeded in advance comes back",
        )

    @override
    def look(
        self, laid: ManyRegistriesAndACaller, answered: Answered[list[ReservoirRegistryNode]]
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                sorted(registry_snapshot(one) for one in items),
                SameAs(
                    sorted(
                        (
                            one.id,
                            one.id,
                            one.name,
                            one.endpoint,
                            one.access_key,
                            one.secret_key,
                            one.api_version,
                        )
                        for one in laid.laid
                    ),
                    Says(
                        "미리 저장한 레지스트리",
                        english="the registries seeded in advance",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class TheOrderIsKept(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 레지스트리는 요청한 순서대로 반환되고, 존재하지 않는 id 의 항목은 비어 "
            "있습니다",
            english=(
                "the registries seeded in advance come back in the requested order, and the "
                "entry for the id that does not exist is empty"
            ),
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
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
                first.name if isinstance(first, ReservoirRegistryNode) else None,
                laid.laid[0].name,
            ),
            Same("[1]", middle, None),
            Same(
                "[2].name",
                last.name if isinstance(last, ReservoirRegistryNode) else None,
                laid.laid[1].name,
            ),
        ]


@dataclass(frozen=True)
class EveryIdIsRefused(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "항목마다 권한 부족 거부가 담겨 반환됩니다",
            english="every entry comes back holding a rejection for lack of permission",
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
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
class AUserGrantedReadGets(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, ReservoirRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-gets-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "Reservoir 레지스트리 조회 권한을 받은 사용자가 하나를 조회하면 미리 저장한 "
            "레지스트리 전체가 반환됩니다",
            english=(
                "when a user granted permission to read Reservoir registries reads one, the "
                "whole registry seeded in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ARegistryAndACaller, ReservoirRegistryAdapter, ReservoirRegistryNode]:
        return Getting()

    @override
    def then(self) -> Then[ARegistryAndACaller, ReservoirRegistryNode]:
        return TheRegistryNode()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotGet(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ReservoirRegistryAdapter, ReservoirRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-get-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 레지스트리를 조회하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to read a registry, it is rejected for lack "
                "of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, ReservoirRegistryAdapter, ReservoirRegistryNode]:
        return Getting()

    @override
    def then(self) -> Then[ARegistryAndACaller, ReservoirRegistryNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadsMany(
    Scenario[
        TestSeedingSession,
        ManyRegistriesAndACaller,
        ReservoirRegistryAdapter,
        list[ReservoirRegistryNode],
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-several-reservoir-registries-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 레지스트리 둘을 id 로 한 번에 조회하면 둘 다 반환됩니다. 이 호출은 "
            "전역 역할을 검사합니다",
            english=(
                "when the superadmin reads two registries by id at once, both come back. This "
                "call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, list[ReservoirRegistryNode]]:
        return ReadingMany()

    @override
    def then(
        self,
    ) -> Then[ManyRegistriesAndACaller, list[ReservoirRegistryNode]]:
        return TheRegistriesAreReturned()


@dataclass(frozen=True)
class APlainUserMayNotReadMany(
    Scenario[
        TestSeedingSession,
        ManyRegistriesAndACaller,
        ReservoirRegistryAdapter,
        list[ReservoirRegistryNode],
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-read-several-registries"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 레지스트리를 id 로 한 번에 조회하려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin reads registries by id at once, it is "
                "rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(
        self,
    ) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, list[ReservoirRegistryNode]]:
        return ReadingMany()

    @override
    def then(
        self,
    ) -> Then[ManyRegistriesAndACaller, list[ReservoirRegistryNode]]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserGrantedReadLoadsManyInOrder(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-loads-several-reservoir-registries-in-the-requested-order"

    @override
    def describe(self) -> str:
        return Says(
            "Reservoir 레지스트리 조회 권한을 받은 사용자가 미리 저장한 레지스트리 둘과 존재하지 않는 "
            "id 하나를 한 번에 조회하면, 둘은 요청한 순서대로 반환되고 존재하지 않는 id 의 항목은 "
            "비어 있습니다",
            english=(
                "when a user granted permission to read Reservoir registries loads two registries "
                "seeded in advance and one id that does not exist at once, the two come back in "
                "the requested order and the entry for the id that does not exist is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return TheOrderIsKept()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedOnEveryId(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ReservoirRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-loading-many-registry-ids-is-refused-on-every-id"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 레지스트리 id 여럿을 한 번에 조회하면, 요청 전체가 "
            "거부되는 대신 항목마다 권한 부족 거부가 담겨 반환됩니다",
            english=(
                "when a user granted nothing loads several registry ids at once, instead of "
                "rejecting the whole request, every entry comes back holding a rejection for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ReservoirRegistryAdapter, Loaded]:
        return LoadingByIds()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return EveryIdIsRefused()


SCENARIOS: list[ReadingStep] = [
    AUserGrantedReadGets(),
    AUserGrantedNothingMayNotGet(),
    TheSuperadminReadsMany(),
    APlainUserMayNotReadMany(),
    AUserGrantedReadLoadsManyInOrder(),
    AUserGrantedNothingIsRefusedOnEveryId(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep,
    adapter: ReservoirRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
