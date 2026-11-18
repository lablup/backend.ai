"""세션, 커널, 커널 그룹과 그 아래 행을 id 로 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironID
from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.kernel.response import KernelNode
from ai.backend.common.dto.manager.v2.kernel_group.response import (
    KernelGroupEnvironNode,
    KernelGroupNode,
    KernelGroupResourceSlotNode,
)
from ai.backend.common.dto.manager.v2.session.response import SessionNode
from ai.backend.common.types import SessionId
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
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
from bai_scenario.components.resource_allocation import Granted
from bai_scenario.components.session_reads import (
    ASessionWithAKernelAndSomeone,
    LaidSessionAndCaller,
    environ_dump,
    group_slot_dump,
    kernel_dump,
    kernel_group_dump,
    session_dump,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type OneSession = SessionNode
type Sessions = list[SessionNode | Exception | None]
type Kernels = list[KernelNode | Exception | None]
type MainGroups = list[KernelGroupNode | None]
type Groups = list[KernelGroupNode | Exception | None]
type Environs = list[KernelGroupEnvironNode | Exception | None]
type Slots = list[KernelGroupResourceSlotNode | Exception | None]


@dataclass(frozen=True)
class ReadingTheSession(When[LaidSessionAndCaller, SessionAdapter, OneSession]):
    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션을 id 로 읽습니다",
            english=f"{laid.caller.username} reads the session {laid.session.name} by id",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> OneSession:
        with ActingAs(laid.caller):
            return await adapter.get(SessionId(laid.session.id))


@dataclass(frozen=True)
class LoadingTheSession(When[LaidSessionAndCaller, SessionAdapter, Sessions]):
    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션을 id 로 일괄 조회합니다",
            english=f"{laid.caller.username} loads the session {laid.session.name} by id",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Sessions:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([SessionID(laid.session.id)])


@dataclass(frozen=True)
class LoadingTheKernel(When[LaidSessionAndCaller, SessionAdapter, Kernels]):
    @override
    def operation(self) -> str:
        return "batch_load_kernels_by_ids"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 커널을 id 로 일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads the kernel of the session {laid.session.name} by id"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Kernels:
        with ActingAs(laid.caller):
            return await adapter.batch_load_kernels_by_ids([KernelID(laid.kernel.id)])


@dataclass(frozen=True)
class LoadingTheMainGroup(When[LaidSessionAndCaller, SessionAdapter, MainGroups]):
    @override
    def operation(self) -> str:
        return "batch_load_main_kernel_groups"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 주 커널 그룹을 세션 id 로 "
            "일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads the main kernel group of the session "
                f"{laid.session.name} by session id"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> MainGroups:
        with ActingAs(laid.caller):
            return await adapter.batch_load_main_kernel_groups([SessionID(laid.session.id)])


@dataclass(frozen=True)
class LoadingTheGroup(When[LaidSessionAndCaller, SessionAdapter, Groups]):
    @override
    def operation(self) -> str:
        return "batch_load_kernel_groups_by_ids"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 커널 그룹을 id 로 일괄 "
            "조회합니다",
            english=(
                f"{laid.caller.username} loads the kernel group of the session "
                f"{laid.session.name} by id"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Groups:
        with ActingAs(laid.caller):
            return await adapter.batch_load_kernel_groups_by_ids([KernelGroupID(laid.group.id)])


@dataclass(frozen=True)
class LoadingTheEnviron(When[LaidSessionAndCaller, SessionAdapter, Environs]):
    @override
    def operation(self) -> str:
        return "batch_load_kernel_group_environs_by_ids"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션 커널 그룹의 환경 변수를 id 로 "
            "일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads an environment variable of the session "
                f"{laid.session.name}'s kernel group by id"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Environs:
        with ActingAs(laid.caller):
            return await adapter.batch_load_kernel_group_environs_by_ids([
                KernelGroupEnvironID(laid.environ.id)
            ])


@dataclass(frozen=True)
class LoadingTheGroupSlot(When[LaidSessionAndCaller, SessionAdapter, Slots]):
    @override
    def operation(self) -> str:
        return "batch_load_kernel_group_resource_slots_by_ids"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션 커널 그룹의 자원 슬롯을 id 로 "
            "일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads a resource slot of the session "
                f"{laid.session.name}'s kernel group by id"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Slots:
        with ActingAs(laid.caller):
            return await adapter.batch_load_kernel_group_resource_slots_by_ids([
                KernelGroupResourceSlotID(laid.group_slot.id)
            ])


def _one_dump(loaded: list[Any] | None, dumped: dict[str, Any], named: Says) -> list[Verdict]:
    if loaded is None:
        return []
    if not loaded:
        return [Same("length", len(loaded), 1)]
    entry = loaded[0]
    if not hasattr(entry, "model_dump"):
        return [Same("[0]", type(entry).__name__, "a node")]
    return [
        Same("length", len(loaded), 1),
        Held("[0]", entry.model_dump(), SameAs(dumped, named)),
    ]


@dataclass(frozen=True)
class TheWholeSession(Then[LaidSessionAndCaller, OneSession]):
    @override
    def says(self) -> str:
        return Says(
            "세션 전체가 저장된 그대로 반환됩니다",
            english="the whole session comes back exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[OneSession]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "session",
                node.model_dump(),
                SameAs(
                    session_dump(laid),
                    Says(
                        "저장된 세션의 전체 정보",
                        english="the whole information of the stored session",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class TheSessionInOneEntry(Then[LaidSessionAndCaller, Sessions]):
    @override
    def says(self) -> str:
        return Says(
            "세션 하나가 저장된 그대로 한 항목으로 반환됩니다",
            english="the session comes back as one entry exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Sessions]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return _one_dump(
            loaded,
            session_dump(laid),
            Says("저장된 세션의 전체 정보", english="the whole information of the stored session"),
        )


@dataclass(frozen=True)
class TheKernelInOneEntry(Then[LaidSessionAndCaller, Kernels]):
    @override
    def says(self) -> str:
        return Says(
            "커널 하나가 저장된 그대로 한 항목으로 반환됩니다",
            english="the kernel comes back as one entry exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Kernels]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return _one_dump(
            loaded,
            kernel_dump(laid.kernel, laid.slot_name, laid.quantity),
            Says("저장된 커널의 전체 정보", english="the whole information of the stored kernel"),
        )


@dataclass(frozen=True)
class TheGroupInOneEntry(Then[LaidSessionAndCaller, Groups]):
    @override
    def says(self) -> str:
        return Says(
            "커널 그룹 하나가 저장된 그대로 한 항목으로 반환됩니다",
            english="the kernel group comes back as one entry exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Groups]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return _one_dump(
            loaded,
            kernel_group_dump(laid.group),
            Says(
                "저장된 커널 그룹의 전체 정보",
                english="the whole information of the stored kernel group",
            ),
        )


@dataclass(frozen=True)
class TheMainGroupInOneEntry(Then[LaidSessionAndCaller, MainGroups]):
    @override
    def says(self) -> str:
        return Says(
            "세션의 주 커널 그룹이 저장된 그대로 한 항목으로 반환됩니다",
            english="the main kernel group of the session comes back as one entry as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[MainGroups]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return _one_dump(
            loaded,
            kernel_group_dump(laid.group),
            Says(
                "저장된 커널 그룹의 전체 정보",
                english="the whole information of the stored kernel group",
            ),
        )


@dataclass(frozen=True)
class TheEnvironInOneEntry(Then[LaidSessionAndCaller, Environs]):
    @override
    def says(self) -> str:
        return Says(
            "환경 변수 하나가 저장된 그대로 한 항목으로 반환됩니다",
            english="the environment variable comes back as one entry as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Environs]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return _one_dump(
            loaded,
            environ_dump(laid.environ),
            Says(
                "저장된 환경 변수 행의 전체 정보",
                english="the whole information of the stored environment variable row",
            ),
        )


@dataclass(frozen=True)
class TheGroupSlotInOneEntry(Then[LaidSessionAndCaller, Slots]):
    @override
    def says(self) -> str:
        return Says(
            "자원 슬롯 행 하나가 저장된 그대로 한 항목으로 반환됩니다",
            english="the resource slot row comes back as one entry as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Slots]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return _one_dump(
            loaded,
            group_slot_dump(laid.group_slot),
            Says(
                "저장된 자원 슬롯 행의 전체 정보",
                english="the whole information of the stored resource slot row",
            ),
        )


@dataclass(frozen=True)
class TheEntryIsRefused(Then[Any, list[Any]]):
    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(self, laid: Any, answered: Answered[list[Any]]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        entry = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, entry if isinstance(entry, Exception) else None),
        ]


def _granted_description(korean: str, english: str, granted: Granted) -> Says:
    """The sentence a row with this grant says about what the call does."""
    if granted is Granted.NOTHING:
        return Says(
            f"아무 권한도 받지 않은 사용자가 {korean}하면, 권한 부족으로 거부됩니다",
            english=(
                f"when a user granted nothing {english}, the call is rejected for lack of "
                "permission"
            ),
        )
    return Says(
        f"그 프로젝트에서 세션 읽기 권한을 받은 사용자가 {korean}하면, 저장된 그대로 반환됩니다",
        english=(
            f"when a user granted session read in the project {english}, it comes back exactly "
            "as it was stored"
        ),
    )


@dataclass(frozen=True)
class ReadingASession(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, OneSession]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-session-is-read-by-id-{self.granted.value}"

    @override
    def describe(self) -> str:
        return _granted_description("세션을 id 로 읽", "reads a session by id", self.granted)

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, OneSession]:
        return ReadingTheSession()

    @override
    def then(self) -> Then[LaidSessionAndCaller, OneSession]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheWholeSession()


@dataclass(frozen=True)
class LoadingASession(Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Sessions]):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-session-is-batch-loaded-by-id-{self.granted.value}"

    @override
    def describe(self) -> str:
        return _granted_description("세션을 id 로 일괄 조회", "loads a session by id", self.granted)

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Sessions]:
        return LoadingTheSession()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Sessions]:
        if self.granted is Granted.NOTHING:
            return TheEntryIsRefused()
        return TheSessionInOneEntry()


@dataclass(frozen=True)
class LoadingAKernel(Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Kernels]):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-kernel-is-batch-loaded-by-id-{self.granted.value}"

    @override
    def describe(self) -> str:
        return _granted_description("커널을 id 로 일괄 조회", "loads a kernel by id", self.granted)

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Kernels]:
        return LoadingTheKernel()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Kernels]:
        if self.granted is Granted.NOTHING:
            return TheEntryIsRefused()
        return TheKernelInOneEntry()


@dataclass(frozen=True)
class LoadingAMainGroup(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, MainGroups]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-main-kernel-group-is-batch-loaded-by-session-id-{self.granted.value}"

    @override
    def describe(self) -> str:
        return _granted_description(
            "세션의 주 커널 그룹을 일괄 조회",
            "loads the main kernel group of a session",
            self.granted,
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, MainGroups]:
        return LoadingTheMainGroup()

    @override
    def then(self) -> Then[LaidSessionAndCaller, MainGroups]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheMainGroupInOneEntry()


@dataclass(frozen=True)
class LoadingAGroup(Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Groups]):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-kernel-group-is-batch-loaded-by-id-{self.granted.value}"

    @override
    def describe(self) -> str:
        return _granted_description(
            "커널 그룹을 id 로 일괄 조회", "loads a kernel group by id", self.granted
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Groups]:
        return LoadingTheGroup()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Groups]:
        if self.granted is Granted.NOTHING:
            return TheEntryIsRefused()
        return TheGroupInOneEntry()


@dataclass(frozen=True)
class LoadingAnEnviron(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Environs]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-kernel-group-environ-is-batch-loaded-by-id-{self.granted.value}"

    @override
    def describe(self) -> str:
        return _granted_description(
            "커널 그룹의 환경 변수를 id 로 일괄 조회",
            "loads a kernel group environ by id",
            self.granted,
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Environs]:
        return LoadingTheEnviron()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Environs]:
        if self.granted is Granted.NOTHING:
            return TheEntryIsRefused()
        return TheEnvironInOneEntry()


@dataclass(frozen=True)
class LoadingAGroupSlot(Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Slots]):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-kernel-group-resource-slot-is-batch-loaded-by-id-{self.granted.value}"

    @override
    def describe(self) -> str:
        return _granted_description(
            "커널 그룹의 자원 슬롯을 id 로 일괄 조회",
            "loads a kernel group resource slot by id",
            self.granted,
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Slots]:
        return LoadingTheGroupSlot()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Slots]:
        if self.granted is Granted.NOTHING:
            return TheEntryIsRefused()
        return TheGroupSlotInOneEntry()


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    ReadingASession(granted=Granted.THE_PROJECT),
    ReadingASession(granted=Granted.NOTHING),
    LoadingASession(granted=Granted.THE_PROJECT),
    LoadingASession(granted=Granted.NOTHING),
    LoadingAKernel(granted=Granted.THE_PROJECT),
    LoadingAKernel(granted=Granted.NOTHING),
    LoadingAMainGroup(granted=Granted.THE_PROJECT),
    LoadingAMainGroup(granted=Granted.NOTHING),
    LoadingAGroup(granted=Granted.THE_PROJECT),
    LoadingAGroup(granted=Granted.NOTHING),
    LoadingAnEnviron(granted=Granted.THE_PROJECT),
    LoadingAnEnviron(granted=Granted.NOTHING),
    LoadingAGroupSlot(granted=Granted.THE_PROJECT),
    LoadingAGroupSlot(granted=Granted.NOTHING),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
