"""레지스트리 여럿을 id 목록으로 읽기, 그리고 DataLoader 모양으로 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact_registry.response import ArtifactRegistryGQLNode
from ai.backend.manager.api.adapters.artifact_registry.adapter import ArtifactRegistryAdapter
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
from bai_scenario.components.artifact_registry import (
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
    registry_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID(int=1)
"""어떤 행도 가리키는 레지스트리가 없는 id."""

type Read = list[ArtifactRegistryGQLNode]
type Loaded = list[ArtifactRegistryGQLNode | Exception | None]


@dataclass(frozen=True)
class ReadingManyMetas(When[ManyRegistriesAndACaller, ArtifactRegistryAdapter, Read]):
    """미리 저장한 레지스트리 둘과, ``include_missing`` 이면 없는 id 하나를 한 번에 읽는다."""

    include_missing: bool = False

    @override
    def operation(self) -> str:
        return "get_registry_metas"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.include_missing:
            return Says(
                f"{who}이 미리 저장한 레지스트리 {len(laid.laid)}개와 없는 id 하나를 한 번에 "
                "읽습니다",
                english=(
                    f"{who} reads {len(laid.laid)} registries made in advance and one id that "
                    "does not exist at once"
                ),
            )
        return Says(
            f"{who}이 미리 저장한 레지스트리 {len(laid.laid)}개를 한 번에 읽습니다",
            english=f"{who} reads {len(laid.laid)} registries made in advance at once",
        )

    def ids(self, laid: ManyRegistriesAndACaller) -> list[UUID]:
        ids = [one.id for one in laid.laid]
        if self.include_missing:
            ids.append(MISSING)
        return ids

    @override
    async def call(self, adapter: ArtifactRegistryAdapter, laid: ManyRegistriesAndACaller) -> Read:
        with ActingAs(laid.caller):
            return await adapter.get_registry_metas(self.ids(laid))


@dataclass(frozen=True)
class LoadingMany(When[ManyRegistriesAndACaller, ArtifactRegistryAdapter, Loaded]):
    """미리 저장한 레지스트리 둘과 없는 id 하나를 DataLoader 모양으로 읽는다."""

    empty: bool = False

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.empty:
            return Says(
                f"{who}이 빈 id 목록으로 읽습니다",
                english=f"{who} loads with an empty id list",
            )
        return Says(
            f"{who}이 미리 저장한 레지스트리 둘과 없는 id 하나를 한 번에 읽습니다",
            english=(
                f"{who} loads two registries made in advance and one id that does not exist at once"
            ),
        )

    def ids(self, laid: ManyRegistriesAndACaller) -> list[ArtifactRegistryID]:
        if self.empty:
            return []
        return [
            ArtifactRegistryID(laid.laid[0].id),
            ArtifactRegistryID(MISSING),
            ArtifactRegistryID(laid.laid[1].id),
        ]

    @override
    async def call(
        self, adapter: ArtifactRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self.ids(laid))


@dataclass(frozen=True)
class EveryReadableRegistryComesBack(Then[ManyRegistriesAndACaller, Read]):
    """읽을 수 있는 레지스트리만 요청한 순서대로 온다. 없는 id 는 빠진다."""

    @override
    def says(self) -> str:
        return Says(
            "읽을 수 있는 레지스트리만 요청한 순서대로 오고, 읽을 수 없거나 없는 id 는 빠집니다",
            english=(
                "only the registries the caller may read come back in the requested order, and "
                "an id that is unreadable or names no registry is left out"
            ),
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Read]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("count", len(got), len(laid.laid))]
        for i, (node, registry) in enumerate(zip(got, laid.laid, strict=False)):
            verdicts += registry_verdicts(f"[{i}].", node, registry)
        return verdicts


@dataclass(frozen=True)
class NoRegistryIsReadable(Then[ManyRegistriesAndACaller, Read]):
    @override
    def says(self) -> str:
        return Says(
            "읽을 수 있는 레지스트리가 없어 빈 목록이 옵니다",
            english="no registry is readable and an empty list comes back",
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Read]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class TheLoadedPositions(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "자리마다 미리 저장한 레지스트리 전체가 오고, 없는 id 자리는 비어 있습니다",
            english=(
                "every position holds a whole registry made in advance, and the position of "
                "the id that does not exist is empty"
            ),
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if len(got) != 3:
            return [Same("length", len(got), 3)]
        first, missing, second = got
        verdicts: list[Verdict] = [Same("length", len(got), 3)]
        if isinstance(first, ArtifactRegistryGQLNode):
            verdicts += registry_verdicts("[0].", first, laid.laid[0])
        else:
            verdicts.append(Same("[0].registry", first, None))
        verdicts.append(Same("[1]", missing, None))
        if isinstance(second, ArtifactRegistryGQLNode):
            verdicts += registry_verdicts("[2].", second, laid.laid[1])
        else:
            verdicts.append(Same("[2].registry", second, None))
        return verdicts


@dataclass(frozen=True)
class EveryPositionIsRefused(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says(
            "자리마다 권한 부족 거부가 담겨 오고, 없는 id 도 같은 거부로 와서 있는지 없는지가 "
            "드러나지 않습니다",
            english=(
                "every position holds a rejection for lack of permission, and the id that does "
                "not exist comes back with the same rejection, so whether it exists is not "
                "revealed"
            ),
        )

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("length", len(got), 3),
            *[
                Refused(NotEnoughPermission, one if isinstance(one, Exception) else None)
                for one in got
            ],
        ]


@dataclass(frozen=True)
class AnEmptyListComesBack(Then[ManyRegistriesAndACaller, Loaded]):
    @override
    def says(self) -> str:
        return Says("빈 응답이 반환됩니다", english="an empty answer comes back")

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class ReadingManyLeavesOutTheMissingOne(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ArtifactRegistryAdapter, Read]
):
    @override
    def summary(self) -> str:
        return "reading-many-registries-leaves-out-the-id-that-names-none"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 레지스트리 읽기 권한을 받은 사용자가 미리 저장한 레지스트리 "
            "둘과 없는 id 하나를 한 번에 읽으면, 읽을 수 있는 레지스트리 둘만 요청한 순서대로 "
            "옵니다",
            english=(
                "when a user granted read permission on artifact registries in global reads two "
                "registries made in advance and one id that does not exist at once, only the two "
                "readable registries come back in the requested order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ArtifactRegistryAdapter, Read]:
        return ReadingManyMetas(include_missing=True)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Read]:
        return EveryReadableRegistryComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingReadsNoRegistry(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ArtifactRegistryAdapter, Read]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-many-registries-gets-none"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 레지스트리 여럿을 한 번에 읽으면, 요청 전체가 "
            "거부되는 대신 읽을 수 있는 레지스트리가 없어 빈 목록이 옵니다",
            english=(
                "when a user granted nothing reads several registries at once, instead of the "
                "whole request being rejected no registry is readable and an empty list comes "
                "back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ArtifactRegistryAdapter, Read]:
        return ReadingManyMetas()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Read]:
        return NoRegistryIsReadable()


@dataclass(frozen=True)
class LoadingKeepsThePositions(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ArtifactRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "loading-many-registry-ids-keeps-the-positions"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 레지스트리 둘과 없는 id 하나를 한 번에 읽으면, 자리마다 "
            "미리 저장한 레지스트리 전체가 오고 없는 id 자리는 비어 있습니다",
            english=(
                "when the superadmin loads two registries made in advance and one id that does "
                "not exist at once, every position holds a whole registry made in advance and "
                "the position of the id that does not exist is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ArtifactRegistryAdapter, Loaded]:
        return LoadingMany()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return TheLoadedPositions()


@dataclass(frozen=True)
class AnEmptyListAsksNothing(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ArtifactRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "an-empty-registry-id-list-answers-empty"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록으로 레지스트리를 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다",
            english=(
                "loading registries with an empty id list calls no lower layer and an empty "
                "answer comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ArtifactRegistryAdapter, Loaded]:
        return LoadingMany(empty=True)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return AnEmptyListComesBack()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedOnEveryPosition(
    Scenario[TestSeedingSession, ManyRegistriesAndACaller, ArtifactRegistryAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-loading-registry-ids-is-refused-on-every-position"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 레지스트리 id 여럿을 한 번에 읽으면, 항목마다 권한 "
            "부족 거부가 담겨 오고 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다",
            english=(
                "when a user granted nothing loads several registry ids at once, every position "
                "holds a rejection for lack of permission, and the id that does not exist comes "
                "back with the same rejection so whether it exists is not revealed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ArtifactRegistryAdapter, Loaded]:
        return LoadingMany()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Loaded]:
        return EveryPositionIsRefused()


SCENARIOS: list[Scenario[TestSeedingSession, Any, ArtifactRegistryAdapter, Any]] = [
    ReadingManyLeavesOutTheMissingOne(),
    AUserGrantedNothingReadsNoRegistry(),
    LoadingKeepsThePositions(),
    AnEmptyListAsksNothing(),
    AUserGrantedNothingIsRefusedOnEveryPosition(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_many(
    scenario: Scenario[TestSeedingSession, Any, ArtifactRegistryAdapter, Any],
    adapter: ArtifactRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
