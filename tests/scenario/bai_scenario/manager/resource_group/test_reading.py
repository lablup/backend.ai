"""리소스 그룹 조회 — 이름으로 하나, id나 이름으로 여럿, 그리고 리소스 현황.

이름으로 id를 찾는 자리는 인증만 확인하므로, 없는 이름은 누구에게나 대상을 찾을 수 없어
거부된다. 권한 검사는 찾은 뒤에 온다.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.response import (
    ResourceGroupDetailNode,
    ResourceInfoNode,
)
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    AGroupAndACaller,
    AGroupAndSomeone,
    EachItemIsRefused,
    GroupLook,
    Loaded,
    ManyGroupsAndACaller,
    NothingComesBack,
    TheGroupNode,
    TheGroupsInTheOrderAsked,
    TheResourceInfoIsEmpty,
    TwoGroupsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ReadingStep = Scenario[TestSeedingSession, Any, ResourceGroupAdapter, Any]

UNKNOWN = "no-such-group"


@dataclass(frozen=True)
class ReadingByName(When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]):
    """이름으로 조회한다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        target_ko = "존재하지 않는 이름" if self.unknown else laid.group.name
        target_en = "a name that does not exist" if self.unknown else laid.group.name
        return Says(
            f"{laid.caller.username}이 {target_ko}으로 조회합니다",
            english=f"{laid.caller.username} reads {target_en}",
        )

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> ResourceGroupDetailNode:
        with ActingAs(laid.caller):
            return await adapter.get(UNKNOWN if self.unknown else laid.group.name)


@dataclass(frozen=True)
class ReadingManyByIds(When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]):
    """미리 만들어 둔 그룹들의 id 뒤에 없는 id 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개와 없는 id 하나를 한 번에 "
            "조회합니다",
            english=(
                f"{laid.caller.username} batch loads {len(laid.laid)} seeded resource groups "
                "and one unknown id"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Loaded:
        ids: Sequence[ResourceGroupID] = [
            *(ResourceGroupID(one.id) for one in laid.laid),
            ResourceGroupID(uuid4()),
        ]
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(ids)


@dataclass(frozen=True)
class ReadingTheLaidByIds(When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]):
    """미리 만들어 둔 그룹들만 id로 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개를 id 로 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch loads the {len(laid.laid)} seeded resource "
                "groups by id"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([ResourceGroupID(one.id) for one in laid.laid])


@dataclass(frozen=True)
class ReadingNoIds(When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]):
    """빈 id 목록으로 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 빈 id 목록으로 조회합니다",
            english=f"{laid.caller.username} batch loads an empty id list",
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([])


@dataclass(frozen=True)
class ReadingManyByNames(When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]):
    """미리 만들어 둔 그룹들의 이름 뒤에 없는 이름 하나를 붙여 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_names"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개와 없는 이름 하나를 한 "
            "번에 조회합니다",
            english=(
                f"{laid.caller.username} batch loads {len(laid.laid)} seeded resource groups "
                "and one unknown name"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_names([*(one.name for one in laid.laid), UNKNOWN])


@dataclass(frozen=True)
class ReadingTheLaidByNames(When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]):
    """미리 만들어 둔 그룹들만 이름으로 한 번에 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_names"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 {len(laid.laid)}개를 이름으로 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} batch loads the {len(laid.laid)} seeded resource "
                "groups by name"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_names([one.name for one in laid.laid])


@dataclass(frozen=True)
class ReadingNoNames(When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]):
    """빈 이름 목록으로 조회한다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_names"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 빈 이름 목록으로 조회합니다",
            english=f"{laid.caller.username} batch loads an empty name list",
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_names([])


@dataclass(frozen=True)
class ReadingResourceInfo(When[AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]):
    """리소스 현황을 조회한다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_resource_info"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        target_ko = "존재하지 않는 이름" if self.unknown else laid.group.name
        target_en = "a name that does not exist" if self.unknown else laid.group.name
        return Says(
            f"{laid.caller.username}이 {target_ko}의 자원 현황을 조회합니다",
            english=f"{laid.caller.username} reads the resource info of {target_en}",
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller) -> ResourceInfoNode:
        with ActingAs(laid.caller):
            return await adapter.get_resource_info(UNKNOWN if self.unknown else laid.group.name)


@dataclass(frozen=True)
class TheSuperadminReadsAGroup(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-resource-group-by-name"

    @override
    def describe(self) -> str:
        return Says(
            "자원 그룹 하나가 있고 superadmin 이 이름으로 조회하면, 그 그룹 전체가 반환됩니다",
            english=(
                "one resource group exists and the superadmin reads it by name, so the whole "
                "group comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedReadOnTheGroupReadsIt(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-group-reads-it-by-name"

    @override
    def describe(self) -> str:
        return Says(
            "그 자원 그룹에 부여된 역할로 읽기 권한을 받은 사용자가 이름으로 조회하면 그 그룹 "
            "전체가 반환됩니다. 자원 그룹이 자기 스코프이므로 자원 그룹에 부여된 역할이 "
            "적용됩니다",
            english=(
                "a user granted read through the role granted on the resource group reading it "
                "by name gets the whole group. the resource group is its own scope, so the role "
                "granted on it applies"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheGroupNode(GroupLook(started=self.started))


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 이름으로 조회하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing reading by name is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadingAnUnknownNameIsNotFound(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reading-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when the superadmin reads a name nothing answers to, the call is rejected "
                "because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return ReadingByName(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(ResourceGroupNotFound)


@dataclass(frozen=True)
class AUserGrantedNothingReadingAnUnknownNameIsNotFoundToo(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-a-name-nothing-answers-to-is-not-found-too"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 존재하지 않는 이름으로 조회해도 권한 부족이 아니라 대상을 "
            "찾을 수 없다는 이유로 거부됩니다. 이름으로 id 를 찾는 단계는 인증만 확인하고 권한 "
            "검사는 찾은 뒤에 옵니다",
            english=(
                "a user granted nothing reading a name nothing answers to is rejected because no "
                "target answers to it, not for not enough permission. the step that looks up the "
                "id by name checks authentication alone and the permission check follows the "
                "lookup"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceGroupDetailNode]:
        return ReadingByName(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceGroupDetailNode]:
        return TheCallIsRefused(ResourceGroupNotFound)


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissingIds(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-by-ids-leaves-a-missing-id-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 그룹 둘과 없는 id 하나를 한 번에 조회하면, 요청한 순서대로 "
            "반환되고 없는 id 에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch loads two seeded groups and one unknown id, the items "
                "come back in the order requested and the item for the unknown id is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]:
        return ReadingManyByIds()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Loaded]:
        return TheGroupsInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerId(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-batch-loading-by-ids-is-refused-per-item"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 그룹 둘을 id 로 한 번에 조회하면, 호출은 거부되지 않고 "
            "항목마다 권한 부족 거부가 담깁니다",
            english=(
                "a user granted nothing batch loading two groups by id is not rejected as a "
                "call, and every item carries a denial for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone()

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]:
        return ReadingTheLaidByIds()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Loaded]:
        return EachItemIsRefused(asked=2)


@dataclass(frozen=True)
class ABatchLoadOfNoIdsAnswersNothing(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록으로 조회하면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다",
            english=(
                "batch loading an empty id list answers an empty response without calling the "
                "lower layer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone()

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]:
        return ReadingNoIds()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Loaded]:
        return NothingComesBack()


@dataclass(frozen=True)
class TheSuperadminLoadsLaidAndMissingNames(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-by-names-leaves-a-missing-name-empty"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 그룹 둘과 없는 이름 하나를 한 번에 조회하면, 요청한 "
            "순서대로 반환되고 없는 이름에 해당하는 항목은 비어 있습니다",
            english=(
                "when the superadmin batch loads two seeded groups and one unknown name, the "
                "items come back in the order requested and the item for the unknown name is "
                "empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]:
        return ReadingManyByNames()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Loaded]:
        return TheGroupsInTheOrderAsked(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingIsRefusedPerName(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-batch-loading-by-names-is-refused-per-item"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 그룹 둘을 이름으로 한 번에 조회하면, 호출은 거부되지 않고 "
            "항목마다 권한 부족 거부가 담깁니다",
            english=(
                "a user granted nothing batch loading two groups by name is not rejected as a "
                "call, and every item carries a denial for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone()

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]:
        return ReadingTheLaidByNames()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Loaded]:
        return EachItemIsRefused(asked=2)


@dataclass(frozen=True)
class ABatchLoadOfNoNamesAnswersNothing(
    Scenario[TestSeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-names-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return Says(
            "빈 이름 목록으로 조회하면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다",
            english=(
                "batch loading an empty name list answers an empty response without calling the "
                "lower layer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone()

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Loaded]:
        return ReadingNoNames()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Loaded]:
        return NothingComesBack()


@dataclass(frozen=True)
class TheSuperadminReadsAnEmptyResourceInfo(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-an-empty-resource-info-of-a-group-without-agents"

    @override
    def describe(self) -> str:
        return Says(
            "에이전트가 없는 그룹의 자원 현황을 superadmin 이 조회하면 용량, 사용량, 여유가 모두 "
            "비어 있습니다",
            english=(
                "when the superadmin reads the resource info of a group without agents, "
                "capacity, used and free are all empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]:
        return ReadingResourceInfo()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceInfoNode]:
        return TheResourceInfoIsEmpty()


@dataclass(frozen=True)
class AUserGrantedReadReadsTheResourceInfo(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-group-reads-its-resource-info"

    @override
    def describe(self) -> str:
        return Says(
            "그 자원 그룹에 부여된 역할로 읽기 권한을 받은 사용자가 자원 현황을 조회하면 "
            "superadmin 과 같은 응답을 받습니다",
            english=(
                "a user granted read through the role granted on the resource group reading the "
                "resource info gets the same response as the superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]:
        return ReadingResourceInfo()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceInfoNode]:
        return TheResourceInfoIsEmpty()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheResourceInfo(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-resource-info"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 자원 현황을 조회하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing reading the resource info is rejected for not enough "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]:
        return ReadingResourceInfo()

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceInfoNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheResourceInfoOfAnUnknownNameIsNotFound(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]
):
    @override
    def summary(self) -> str:
        return "the-resource-info-of-a-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 존재하지 않는 이름의 자원 현황을 조회하면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when the superadmin reads the resource info of a name nothing answers to, the "
                "call is rejected because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, ResourceInfoNode]:
        return ReadingResourceInfo(unknown=True)

    @override
    def then(self) -> Then[AGroupAndACaller, ResourceInfoNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsAGroup(started=datetime.now(UTC)),
    AUserGrantedReadOnTheGroupReadsIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    TheSuperadminReadingAnUnknownNameIsNotFound(),
    AUserGrantedNothingReadingAnUnknownNameIsNotFoundToo(),
    TheSuperadminLoadsLaidAndMissingIds(started=datetime.now(UTC)),
    AUserGrantedNothingIsRefusedPerId(),
    ABatchLoadOfNoIdsAnswersNothing(),
    TheSuperadminLoadsLaidAndMissingNames(started=datetime.now(UTC)),
    AUserGrantedNothingIsRefusedPerName(),
    ABatchLoadOfNoNamesAnswersNothing(),
    TheSuperadminReadsAnEmptyResourceInfo(),
    AUserGrantedReadReadsTheResourceInfo(),
    AUserGrantedNothingMayNotReadTheResourceInfo(),
    TheResourceInfoOfAnUnknownNameIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
