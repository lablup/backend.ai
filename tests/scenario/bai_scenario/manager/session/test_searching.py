"""세션과 커널, 커널 그룹의 검색."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.kernel.request import (
    AdminSearchKernelsInput,
    KernelFilter,
    KernelOrder,
)
from ai.backend.common.dto.manager.v2.kernel.response import AdminSearchKernelsPayload
from ai.backend.common.dto.manager.v2.kernel.types import KernelOrderField
from ai.backend.common.dto.manager.v2.kernel_group.request import (
    KernelGroupEnvironOrder,
    KernelGroupOrder,
    KernelGroupResourceSlotOrder,
    ScopedSearchKernelGroupEnvironsInput,
    ScopedSearchKernelGroupResourceSlotsInput,
    ScopedSearchKernelGroupsInput,
)
from ai.backend.common.dto.manager.v2.kernel_group.response import (
    ScopedSearchKernelGroupEnvironsPayload,
    ScopedSearchKernelGroupResourceSlotsPayload,
    ScopedSearchKernelGroupsPayload,
)
from ai.backend.common.dto.manager.v2.kernel_group.types import (
    KernelGroupEnvironOrderField,
    KernelGroupEnvironScope,
    KernelGroupOrderField,
    KernelGroupResourceSlotOrderField,
    KernelGroupResourceSlotScope,
    KernelGroupScope,
)
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    ScopedSearchSessionsInput,
    SessionFilter,
    SessionOrder,
)
from ai.backend.common.dto.manager.v2.session.response import AdminSearchSessionsPayload
from ai.backend.common.dto.manager.v2.session.types import SessionOrderField, SessionScope
from ai.backend.common.types import SessionId
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
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

type Kernels = AdminSearchKernelsPayload
type Sessions = AdminSearchSessionsPayload
type Groups = ScopedSearchKernelGroupsPayload
type Environs = ScopedSearchKernelGroupEnvironsPayload
type Slots = ScopedSearchKernelGroupResourceSlotsPayload

PAGE = 10
"""The page size every search asks for, larger than what the row seeds."""


@dataclass(frozen=True)
class SearchingEveryKernel(When[LaidSessionAndCaller, SessionAdapter, Kernels]):
    @override
    def operation(self) -> str:
        return "admin_search_kernels"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 필터 없이 모든 커널을 조회합니다",
            english=f"{laid.caller.username} searches every kernel without a filter",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Kernels:
        with ActingAs(laid.caller):
            return await adapter.admin_search_kernels(
                AdminSearchKernelsInput(
                    filter=KernelFilter(session_id=UUIDFilter(equals=laid.session.id)),
                    order=[
                        KernelOrder(
                            field=KernelOrderField.CREATED_AT, direction=OrderDirection.ASC
                        )
                    ],
                    limit=PAGE,
                )
            )


@dataclass(frozen=True)
class SearchingTheSessionKernels(When[LaidSessionAndCaller, SessionAdapter, Kernels]):
    @override
    def operation(self) -> str:
        return "search_kernels_by_session"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 커널을 조회합니다",
            english=f"{laid.caller.username} searches the kernels of {laid.session.name}",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Kernels:
        with ActingAs(laid.caller):
            return await adapter.search_kernels_by_session(
                SessionId(laid.session.id),
                AdminSearchKernelsInput(
                    order=[
                        KernelOrder(
                            field=KernelOrderField.CREATED_AT, direction=OrderDirection.ASC
                        )
                    ],
                    limit=PAGE,
                ),
            )


@dataclass(frozen=True)
class SearchingTheProject(When[LaidSessionAndCaller, SessionAdapter, Sessions]):
    operation_name: str

    @override
    def operation(self) -> str:
        return self.operation_name

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        if self.operation_name == "gql_search_by_project":
            return Says(
                f"{laid.caller.username}이 {laid.project.name} 프로젝트의 세션을 조회합니다",
                english=f"{laid.caller.username} searches the sessions of {laid.project.name}",
            )
        if self.operation_name == "project_search":
            return Says(
                f"{laid.caller.username}이 {laid.project.name} 프로젝트 id 로 세션을 조회합니다",
                english=(
                    f"{laid.caller.username} searches sessions by the project id of "
                    f"{laid.project.name}"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {laid.project.name} 프로젝트 스코프에서 세션을 조회합니다",
            english=(
                f"{laid.caller.username} searches sessions in the scope of {laid.project.name}"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Sessions:
        with ActingAs(laid.caller):
            if self.operation_name == "gql_search_by_project":
                return await adapter.gql_search_by_project(
                    ProjectID(laid.project.id), self._admin_input(laid)
                )
            if self.operation_name == "project_search":
                return await adapter.project_search(laid.project.id, self._admin_input(laid))
            return await adapter.scoped_search(
                ScopedSearchSessionsInput(
                    scope=SessionScope(project=[UUIDScope(value=laid.project.id)]),
                    filter=SessionFilter(name=StringFilter(equals=laid.session.name)),
                    order=[
                        SessionOrder(
                            field=SessionOrderField.NAME, direction=OrderDirection.ASC
                        )
                    ],
                    limit=PAGE,
                )
            )

    def _admin_input(self, laid: LaidSessionAndCaller) -> AdminSearchSessionsInput:
        return AdminSearchSessionsInput(
            filter=SessionFilter(name=StringFilter(equals=laid.session.name)),
            order=[SessionOrder(field=SessionOrderField.NAME, direction=OrderDirection.ASC)],
            limit=PAGE,
        )


@dataclass(frozen=True)
class SearchingTheGroups(When[LaidSessionAndCaller, SessionAdapter, Groups]):
    @override
    def operation(self) -> str:
        return "scoped_search_kernel_groups"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 커널 그룹을 조회합니다",
            english=f"{laid.caller.username} searches the kernel groups of {laid.session.name}",
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Groups:
        with ActingAs(laid.caller):
            return await adapter.scoped_search_kernel_groups(
                ScopedSearchKernelGroupsInput(
                    scope=KernelGroupScope(session=[UUIDScope(value=laid.session.id)]),
                    order=[
                        KernelGroupOrder(
                            field=KernelGroupOrderField.ROLE, direction=OrderDirection.ASC
                        )
                    ],
                    limit=PAGE,
                )
            )


@dataclass(frozen=True)
class SearchingTheEnvirons(When[LaidSessionAndCaller, SessionAdapter, Environs]):
    @override
    def operation(self) -> str:
        return "scoped_search_kernel_group_environs"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션 커널 그룹의 환경 변수를 조회합니다",
            english=(
                f"{laid.caller.username} searches the environment variables of "
                f"{laid.session.name}'s kernel groups"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Environs:
        with ActingAs(laid.caller):
            return await adapter.scoped_search_kernel_group_environs(
                ScopedSearchKernelGroupEnvironsInput(
                    scope=KernelGroupEnvironScope(session=[UUIDScope(value=laid.session.id)]),
                    order=[
                        KernelGroupEnvironOrder(
                            field=KernelGroupEnvironOrderField.KEY,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=PAGE,
                )
            )


@dataclass(frozen=True)
class SearchingTheGroupSlots(When[LaidSessionAndCaller, SessionAdapter, Slots]):
    @override
    def operation(self) -> str:
        return "scoped_search_kernel_group_resource_slots"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션 커널 그룹의 자원 슬롯을 조회합니다",
            english=(
                f"{laid.caller.username} searches the resource slots of "
                f"{laid.session.name}'s kernel groups"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> Slots:
        with ActingAs(laid.caller):
            return await adapter.scoped_search_kernel_group_resource_slots(
                ScopedSearchKernelGroupResourceSlotsInput(
                    scope=KernelGroupResourceSlotScope(session=[UUIDScope(value=laid.session.id)]),
                    order=[
                        KernelGroupResourceSlotOrder(
                            field=KernelGroupResourceSlotOrderField.SLOT_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=PAGE,
                )
            )


def _page_verdicts(loaded: Any, dumped: list[dict[str, Any]], named: Says) -> list[Verdict]:
    return [
        Held("items", [node.model_dump() for node in loaded.items], SameAs(dumped, named)),
        Same("total_count", loaded.total_count, len(dumped)),
        Same("has_next_page", loaded.has_next_page, False),
        Same("has_previous_page", loaded.has_previous_page, False),
    ]


@dataclass(frozen=True)
class TheKernelPage(Then[LaidSessionAndCaller, Kernels]):
    @override
    def says(self) -> str:
        return Says(
            "세션의 커널 전체가 저장된 그대로 반환됩니다",
            english="the kernel comes back exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Kernels]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        return _page_verdicts(
            page,
            [kernel_dump(laid.kernel, laid.slot_name, laid.quantity)],
            Says("저장된 커널의 전체 정보", english="the whole information of the stored kernel"),
        )


@dataclass(frozen=True)
class TheSessionPage(Then[LaidSessionAndCaller, Sessions]):
    @override
    def says(self) -> str:
        return Says(
            "그 프로젝트의 세션 전체가 저장된 그대로 반환됩니다",
            english="the session of the project comes back exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Sessions]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        return _page_verdicts(
            page,
            [session_dump(laid)],
            Says("저장된 세션의 전체 정보", english="the whole information of the stored session"),
        )


@dataclass(frozen=True)
class TheGroupPage(Then[LaidSessionAndCaller, Groups]):
    @override
    def says(self) -> str:
        return Says(
            "세션의 커널 그룹 전체가 저장된 그대로 반환됩니다",
            english="the kernel group comes back exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Groups]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        return _page_verdicts(
            page,
            [kernel_group_dump(laid.group)],
            Says(
                "저장된 커널 그룹의 전체 정보",
                english="the whole information of the stored kernel group",
            ),
        )


@dataclass(frozen=True)
class TheEnvironPage(Then[LaidSessionAndCaller, Environs]):
    @override
    def says(self) -> str:
        return Says(
            "세션 커널 그룹의 환경 변수 전체가 저장된 그대로 반환됩니다",
            english="the environment variable comes back exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Environs]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        return _page_verdicts(
            page,
            [environ_dump(laid.environ)],
            Says(
                "저장된 환경 변수 행의 전체 정보",
                english="the whole information of the stored environment variable row",
            ),
        )


@dataclass(frozen=True)
class TheGroupSlotPage(Then[LaidSessionAndCaller, Slots]):
    @override
    def says(self) -> str:
        return Says(
            "세션 커널 그룹의 자원 슬롯 전체가 저장된 그대로 반환됩니다",
            english="the resource slot row comes back exactly as it was stored",
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[Slots]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        return _page_verdicts(
            page,
            [group_slot_dump(laid.group_slot)],
            Says(
                "저장된 자원 슬롯 행의 전체 정보",
                english="the whole information of the stored resource slot row",
            ),
        )


@dataclass(frozen=True)
class SearchingEveryKernelAsTheSuperadmin(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Kernels]
):
    superadmin: bool

    @override
    def summary(self) -> str:
        who = "superadmin" if self.superadmin else "a-user-who-is-not-a-superadmin"
        return f"{who}-searches-every-kernel"

    @override
    def describe(self) -> str:
        if self.superadmin:
            return Says(
                "아무 권한도 받지 않은 superadmin 이 커널을 전체 검색하면, 저장된 커널 전체가 "
                "반환됩니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다",
                english=(
                    "when a superadmin holding no permission searches every kernel, the stored "
                    "kernel comes back; a role checks this operation, so the requesting user is "
                    "a superadmin"
                ),
            )
        return Says(
            "superadmin 이 아닌 사용자가 커널을 전체 검색하면, 역할 부족으로 거부됩니다",
            english=(
                "when a user who is not a superadmin searches every kernel, the role rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        if self.superadmin:
            return ASessionWithAKernelAndSomeone(
                granted=Granted.NOTHING,
                role=UserRole.SUPERADMIN,
                beside_another_outside=True,
            )
        return ASessionWithAKernelAndSomeone(granted=Granted.NOTHING)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Kernels]:
        return SearchingEveryKernel()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Kernels]:
        if self.superadmin:
            return TheKernelPage()
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class SearchingTheKernelsOfASession(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Kernels]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"the-kernels-of-a-session-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션의 커널을 조회하면, 권한 부족으로 거부됩니다",
                english=(
                    "when a user granted nothing searches the kernels of a session, the call is "
                    "rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 커널을 조회하면, 저장된 "
            "커널 전체가 반환됩니다",
            english=(
                "when a user granted session read in the project searches the kernels of a "
                "session, the stored kernel comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(
            granted=self.granted,
            beside_another_outside=self.granted is not Granted.NOTHING,
        )

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Kernels]:
        return SearchingTheSessionKernels()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Kernels]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheKernelPage()


@dataclass(frozen=True)
class SearchingTheSessionsOfAProject(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Sessions]
):
    operation_name: str = "gql_search_by_project"
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"{self.operation_name}-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 프로젝트 스코프에서 세션을 조회하면, 권한 "
                "부족으로 거부됩니다",
                english=(
                    "when a user granted nothing searches sessions in a project scope, the call "
                    "is rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 프로젝트 스코프에서 세션을 "
            "조회하면, 저장된 세션 전체가 반환됩니다",
            english=(
                "when a user granted session read in the project searches sessions in that "
                "project's scope, the stored session comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(
            granted=self.granted,
            beside_another_outside=self.granted is not Granted.NOTHING,
        )

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Sessions]:
        return SearchingTheProject(operation_name=self.operation_name)

    @override
    def then(self) -> Then[LaidSessionAndCaller, Sessions]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheSessionPage()


@dataclass(frozen=True)
class SearchingTheGroupsOfASession(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Groups]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"the-kernel-groups-of-a-session-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션의 커널 그룹을 조회하면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing searches the kernel groups of a session, the "
                    "call is rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 커널 그룹을 조회하면, "
            "저장된 커널 그룹 전체가 반환됩니다",
            english=(
                "when a user granted session read in the project searches the kernel groups of "
                "a session, the stored kernel group comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(
            granted=self.granted,
            beside_another_outside=self.granted is not Granted.NOTHING,
        )

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Groups]:
        return SearchingTheGroups()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Groups]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheGroupPage()


@dataclass(frozen=True)
class SearchingTheEnvironsOfASession(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Environs]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"the-kernel-group-environs-of-a-session-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션 커널 그룹의 환경 변수를 조회하면, 권한 "
                "부족으로 거부됩니다",
                english=(
                    "when a user granted nothing searches the environment variables of a "
                    "session's kernel groups, the call is rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션 커널 그룹의 환경 변수를 "
            "조회하면, 저장된 환경 변수 전체가 반환됩니다",
            english=(
                "when a user granted session read in the project searches the environment "
                "variables of a session's kernel groups, the stored environment variable "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(
            granted=self.granted,
            beside_another_outside=self.granted is not Granted.NOTHING,
        )

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Environs]:
        return SearchingTheEnvirons()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Environs]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheEnvironPage()


@dataclass(frozen=True)
class SearchingTheGroupSlotsOfASession(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, Slots]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"the-kernel-group-resource-slots-of-a-session-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션 커널 그룹의 자원 슬롯을 조회하면, 권한 "
                "부족으로 거부됩니다",
                english=(
                    "when a user granted nothing searches the resource slots of a session's "
                    "kernel groups, the call is rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션 커널 그룹의 자원 슬롯을 "
            "조회하면, 저장된 자원 슬롯 전체가 반환됩니다",
            english=(
                "when a user granted session read in the project searches the resource slots "
                "of a session's kernel groups, the stored resource slot comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(
            granted=self.granted,
            beside_another_outside=self.granted is not Granted.NOTHING,
        )

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, Slots]:
        return SearchingTheGroupSlots()

    @override
    def then(self) -> Then[LaidSessionAndCaller, Slots]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheGroupSlotPage()


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    SearchingEveryKernelAsTheSuperadmin(superadmin=True),
    SearchingEveryKernelAsTheSuperadmin(superadmin=False),
    SearchingTheKernelsOfASession(granted=Granted.THE_PROJECT),
    SearchingTheKernelsOfASession(granted=Granted.NOTHING),
    SearchingTheSessionsOfAProject(operation_name="gql_search_by_project"),
    SearchingTheSessionsOfAProject(operation_name="gql_search_by_project", granted=Granted.NOTHING),
    SearchingTheSessionsOfAProject(operation_name="project_search"),
    SearchingTheSessionsOfAProject(operation_name="project_search", granted=Granted.NOTHING),
    SearchingTheSessionsOfAProject(operation_name="scoped_search"),
    SearchingTheSessionsOfAProject(operation_name="scoped_search", granted=Granted.NOTHING),
    SearchingTheGroupsOfASession(granted=Granted.THE_PROJECT),
    SearchingTheGroupsOfASession(granted=Granted.NOTHING),
    SearchingTheEnvironsOfASession(granted=Granted.THE_PROJECT),
    SearchingTheEnvironsOfASession(granted=Granted.NOTHING),
    SearchingTheGroupSlotsOfASession(granted=Granted.THE_PROJECT),
    SearchingTheGroupSlotsOfASession(granted=Granted.NOTHING),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
