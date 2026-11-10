"""컨테이너 레지스트리 수정 결과와 수정 후 유효성 검사."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AllowedGroupsInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import ContainerRegistryNode
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.container_registry import (
    InvalidContainerRegistryProject,
    InvalidContainerRegistryURL,
)
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Language,
    Says,
    Scenario,
    Then,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    ARegistryAndACaller,
    ARegistryAndSomeone,
    MissingRegistry,
    RegistryTarget,
    TestSeededRegistry,
    TheUpdatedRegistryNode,
    allowed_project_count,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type EditingScenario = Scenario[
    TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
]


@dataclass(frozen=True)
class Editing(When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]):
    url: str | None = None
    registry_type: ContainerRegistryType | None = None
    project: str | None = None
    allow_project: bool = False
    target: RegistryTarget = field(default_factory=TestSeededRegistry)

    @override
    def operation(self) -> str:
        return "admin_update"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        who = laid.caller.username
        if isinstance(self.target, MissingRegistry):
            target = self.target.says()
            return Says(
                f"{who}이 {target}를 수정합니다",
                english=f"{who} updates {in_language(target, Language.ENGLISH)}",
            )
        if self.url is not None:
            return Says(
                f"{who}이 주소를 {self.url}로 수정합니다",
                english=f"{who} changes the address to {self.url}",
            )
        if self.registry_type is not None:
            return Says(
                f"{who}이 종류를 {self.registry_type.value}로 수정합니다",
                english=f"{who} changes the type to {self.registry_type.value}",
            )
        if self.allow_project:
            return Says(
                f"{who}이 미리 저장한 프로젝트를 허용 목록에 넣으며 수정합니다",
                english=(
                    f"{who} updates it while adding the project seeded in advance to the allow list"
                ),
            )
        return Says(
            f"{who}이 아무 값도 지정하지 않고 수정합니다",
            english=f"{who} updates without naming any value",
        )

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryAndACaller
    ) -> ContainerRegistryNode:
        registry_id = self.target.id_of(laid)
        allowed_groups = None
        if self.allow_project:
            assert laid.project is not None
            allowed_groups = AllowedGroupsInput(add=[str(laid.project.id)])
        with ActingAs(laid.caller):
            payload = await adapter.admin_update(
                UpdateContainerRegistryInput(
                    id=registry_id,
                    url=self.url,
                    type=self.registry_type,
                    project=self.project,
                    allowed_groups=allowed_groups,
                )
            )
        return payload.registry


@dataclass(frozen=True)
class ChangingOnlyTheAddress(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "changing-only-the-address-leaves-every-other-field-alone"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 주소만 수정하면 주소만 새 값이 되고 나머지 필드는 그대로입니다",
            english=(
                "when the superadmin changes only the address, only the address takes the "
                "new value and every other field stays as it is"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> Editing:
        return Editing(url="https://moved.scenario.local")

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheUpdatedRegistryNode(url=self.when().url)


@dataclass(frozen=True)
class AnEmptyEditChangesNothing(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "an-edit-that-names-no-value-changes-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 값을 하나도 지정하지 않고 수정하면 아무것도 바뀌지 않은 노드가 "
            "반환됩니다",
            english=(
                "when the superadmin updates without naming a value, the node comes back "
                "with nothing changed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing()

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheUpdatedRegistryNode()


@dataclass(frozen=True)
class AddingAllowedProjectWhileEditing(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "editing-a-registry-can-add-an-allowed-project"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 컨테이너 레지스트리를 수정하며 프로젝트를 허용하면 그 관계가 생성됩니다",
            english=(
                "when the superadmin updates a container registry and allows a project, "
                "that relation is created"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN, with_project=True)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(allow_project=True)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheUpdatedRegistryNode()


@dataclass(frozen=True)
class AnAddressWithoutAHostIsRefused(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "an-address-whose-host-is-empty-is-refused-on-update"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 호스트가 없는 주소로 수정하려 하면, 수정 후의 row 를 검사하는 단계에서 "
            "주소 형식 에러로 거부됩니다",
            english=(
                "when the superadmin tries to change the address to one without a host, the "
                "step that validates the updated row rejects it as a malformed address"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(url="http://")

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InvalidContainerRegistryURL)


@dataclass(frozen=True)
class HarborWithoutAProjectIsRefused(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "turning-a-registry-into-harbor-without-a-project-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트가 비어 있는 컨테이너 레지스트리를 harbor 종류로 수정하려 하면, "
            "harbor 는 프로젝트를 요구하므로 거부됩니다",
            english=(
                "when a container registry with an empty project is changed to the harbor "
                "type, it is rejected because harbor requires a project"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(registry_type=ContainerRegistryType.HARBOR2)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InvalidContainerRegistryProject)


@dataclass(frozen=True)
class MissingRegistryIsRefused(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "editing-an-id-that-holds-no-registry-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 id 를 수정하려 하면 대상을 찾을 수 없어 거부됩니다",
            english="when an id that does not exist is updated, it is rejected because the target cannot be found",
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(url="https://moved.scenario.local", target=MissingRegistry())

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(ContainerRegistryNotFound)


@dataclass(frozen=True)
class APlainUserMayNotEdit(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-edit-a-registry"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 컨테이너 레지스트리를 수정하려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 호출자가 superadmin 인지만 검사하고 부여된 권한은 보지 않습니다",
            english=(
                "when a user who is not the superadmin tries to edit a container registry, "
                "it is rejected for lack of permission. This call checks only whether the "
                "caller is the superadmin and does not look at the permissions granted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryNode]:
        return Editing(url="https://moved.scenario.local")

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryNode]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[EditingScenario] = [
    ChangingOnlyTheAddress(),
    AnEmptyEditChangesNothing(),
    AddingAllowedProjectWhileEditing(),
    AnAddressWithoutAHostIsRefused(),
    HarborWithoutAProjectIsRefused(),
    MissingRegistryIsRefused(),
    APlainUserMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: EditingScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
    expected_count = 1 if isinstance(scenario, AddingAllowedProjectWhileEditing) else 0
    assert await allowed_project_count(engine) == expected_count
