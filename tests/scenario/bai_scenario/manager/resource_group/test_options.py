"""기본 옵션 갈아끼우기 — 준 것이 통째로 남고, 등록된 처리기만 받는다.

처리기 이름은 등록된 처리기에서 읽는다. 이 모듈이 적는 이름은 등록되지 않은 하나뿐이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentHandlerOptionsInput,
    DeploymentOptionsInput,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ReplaceResourceGroupDefaultDeploymentOptionsInput,
    ReplaceResourceGroupDefaultSessionOptionsInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    ReplaceResourceGroupDefaultDeploymentOptionsPayload,
    ReplaceResourceGroupDefaultSessionOptionsPayload,
)
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options.request import (
    DefaultSessionOptionsInput,
    HandlerOptionsEntryInput,
    HandlerOptionsInput,
    SessionHandlerOptionsInput,
)
from ai.backend.common.dto.manager.v2.session_options.types import (
    AgentSelectionPolicyEnum,
    FailurePolicyEnum,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.deployment.handlers.replica import CheckReplicaDeploymentHandler
from ai.backend.manager.sokovan.scheduler.handlers.lifecycle.terminate_sessions import (
    TerminateSessionsLifecycleHandler,
)
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import AGroupAndACaller, AGroupAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deployed = ReplaceResourceGroupDefaultDeploymentOptionsPayload
type Sessioned = ReplaceResourceGroupDefaultSessionOptionsPayload
type OptionsStep = Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Any]

DEPLOYMENT_HANDLER = CheckReplicaDeploymentHandler.name()
SESSION_HANDLER = TerminateSessionsLifecycleHandler.name()
UNREGISTERED = "no-such-handler"
WAITS = 600
RETRIES = 3
HANDLER_WAITS = 60
PRIORITY = 20


@dataclass(frozen=True)
class ReplacingDeploymentOptions(When[AGroupAndACaller, ResourceGroupAdapter, Deployed]):
    """기본 배포 옵션을 준 것으로 갈아끼운다. ``unregistered``면 등록되지 않은 처리기 이름을 담는다."""

    unregistered: bool = False

    @override
    def operation(self) -> str:
        return "admin_replace_default_deployment_options"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        handler = UNREGISTERED if self.unregistered else DEPLOYMENT_HANDLER
        return Says(
            f"{laid.caller.username}이 {laid.group.name}의 기본 배포 옵션을 선택 정책 STRICT 와 "
            f"처리기 {handler}의 설정을 담아 교체합니다",
            english=(
                f"{laid.caller.username} replaces the default deployment options of "
                f"{laid.group.name} with the selection policy STRICT and the settings of "
                f"handler {handler}"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller) -> Deployed:
        asked = ReplaceResourceGroupDefaultDeploymentOptionsInput(
            options=DeploymentOptionsInput(
                handler_options=DeploymentHandlerOptionsInput(
                    default=HandlerOptionsInput(timeout_sec=WAITS, max_retry_count=RETRIES),
                    by_handler=[
                        HandlerOptionsEntryInput(
                            handler_name=UNREGISTERED if self.unregistered else DEPLOYMENT_HANDLER,
                            timeout_sec=HANDLER_WAITS,
                        )
                    ],
                ),
                agent_selection_policy=AgentSelectionPolicyEnum.STRICT,
            )
        )
        with ActingAs(laid.caller):
            return await adapter.admin_replace_default_deployment_options(
                ResourceGroupName(laid.group.name), asked
            )


@dataclass(frozen=True)
class ReplacingSessionOptions(When[AGroupAndACaller, ResourceGroupAdapter, Sessioned]):
    """기본 세션 옵션을 준 것으로 갈아끼운다. ``unregistered``면 등록되지 않은 처리기 이름을 담는다."""

    unregistered: bool = False

    @override
    def operation(self) -> str:
        return "admin_replace_default_session_options"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        handler = UNREGISTERED if self.unregistered else SESSION_HANDLER
        return Says(
            f"{laid.caller.username}이 {laid.group.name}의 기본 세션 옵션을 우선순위와 처리기 "
            f"{handler}의 설정을 담아 교체합니다",
            english=(
                f"{laid.caller.username} replaces the default session options of "
                f"{laid.group.name} with a priority and the settings of handler {handler}"
            ),
        )

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller) -> Sessioned:
        asked = ReplaceResourceGroupDefaultSessionOptionsInput(
            options=DefaultSessionOptionsInput(
                priority=PRIORITY,
                handler_options=SessionHandlerOptionsInput(
                    default=HandlerOptionsInput(timeout_sec=WAITS, max_retry_count=RETRIES),
                    by_handler=[
                        HandlerOptionsEntryInput(
                            handler_name=UNREGISTERED if self.unregistered else SESSION_HANDLER,
                            timeout_sec=HANDLER_WAITS,
                        )
                    ],
                ),
            )
        )
        with ActingAs(laid.caller):
            return await adapter.admin_replace_default_session_options(
                ResourceGroupName(laid.group.name), asked
            )


@dataclass(frozen=True)
class TheDeploymentOptionsAreReplaced(Then[AGroupAndACaller, Deployed]):
    """준 배포 옵션이 통째로 반환된다. 그룹 전체가 아니라 옵션만 싣는다."""

    @override
    def says(self) -> str:
        return Says(
            "교체한 배포 옵션만 반환됩니다",
            english="only the replaced deployment options come back",
        )

    @override
    def look(self, laid: AGroupAndACaller, answered: Answered[Deployed]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        handler = payload.default_deployment_options.handler_options
        return [
            Same("resource_group_name", payload.resource_group_name, laid.group.name),
            Same(
                "default_deployment_options.handler_options.default.timeout_sec",
                handler.default.timeout_sec,
                WAITS,
            ),
            Same(
                "default_deployment_options.handler_options.default.max_retry_count",
                handler.default.max_retry_count,
                RETRIES,
            ),
            Same(
                "default_deployment_options.handler_options.by_handler",
                [(e.handler_name, e.timeout_sec, e.max_retry_count) for e in handler.by_handler],
                [(DEPLOYMENT_HANDLER, HANDLER_WAITS, None)],
            ),
            Same(
                "default_deployment_options.agent_selection_policy",
                payload.default_deployment_options.agent_selection_policy,
                AgentSelectionPolicyEnum.STRICT,
            ),
        ]


@dataclass(frozen=True)
class TheSessionOptionsAreReplaced(Then[AGroupAndACaller, Sessioned]):
    """준 세션 옵션이 통째로 반환된다. 주지 않은 자리는 코드의 기본값이다."""

    @override
    def says(self) -> str:
        return Says(
            "교체한 세션 옵션만 반환됩니다",
            english="only the replaced session options come back",
        )

    @override
    def look(self, laid: AGroupAndACaller, answered: Answered[Sessioned]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        options = payload.default_session_options
        handler = options.handler_options
        return [
            Same("resource_group_name", payload.resource_group_name, laid.group.name),
            Same("default_session_options.priority", options.priority, PRIORITY),
            Same("default_session_options.is_preemptible", options.is_preemptible, True),
            Same(
                "default_session_options.cluster_mode",
                options.cluster_mode,
                ClusterModeEnum.SINGLE_NODE,
            ),
            Same(
                "default_session_options.default_failure_policy",
                options.default_failure_policy,
                FailurePolicyEnum.STRICT,
            ),
            Same(
                "default_session_options.default_kernel_execution_spec",
                options.default_kernel_execution_spec,
                None,
            ),
            Same(
                "default_session_options.handler_options.default.timeout_sec",
                handler.default.timeout_sec,
                WAITS,
            ),
            Same(
                "default_session_options.handler_options.default.max_retry_count",
                handler.default.max_retry_count,
                RETRIES,
            ),
            Same(
                "default_session_options.handler_options.by_handler",
                [(e.handler_name, e.timeout_sec, e.max_retry_count) for e in handler.by_handler],
                [(SESSION_HANDLER, HANDLER_WAITS, None)],
            ),
            Same(
                "default_session_options.agent_selection_policy",
                options.agent_selection_policy,
                AgentSelectionPolicyEnum.PREFERRED,
            ),
        ]


@dataclass(frozen=True)
class TheSuperadminReplacesTheDeploymentOptions(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Deployed]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-replaces-the-default-deployment-options-whole"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 등록된 처리기 하나의 설정을 담아 기본 배포 옵션을 교체하면 지정한 "
            "옵션 전체가 반환됩니다",
            english=(
                "when the superadmin replaces the default deployment options with the settings "
                "of one registered handler, the options given come back whole"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, Deployed]:
        return ReplacingDeploymentOptions()

    @override
    def then(self) -> Then[AGroupAndACaller, Deployed]:
        return TheDeploymentOptionsAreReplaced()


@dataclass(frozen=True)
class AnUnregisteredDeploymentHandlerIsRefused(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Deployed]
):
    @override
    def summary(self) -> str:
        return "naming-an-unregistered-deployment-handler-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "등록되지 않은 배포 처리기 이름을 담아 교체하려 하면 잘못된 입력으로 거부됩니다",
            english=(
                "replacing the options with the name of an unregistered deployment handler is "
                "rejected as invalid input"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, Deployed]:
        return ReplacingDeploymentOptions(unregistered=True)

    @override
    def then(self) -> Then[AGroupAndACaller, Deployed]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AUserGrantedUpdateReplacesTheDeploymentOptions(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Deployed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-the-group-replaces-the-default-deployment-options"

    @override
    def describe(self) -> str:
        return Says(
            "그 자원 그룹에 부여된 역할로 수정 권한을 받은 사용자가 기본 배포 옵션을 "
            "교체하면 지정한 옵션 전체가 반환됩니다",
            english=(
                "a user granted update through the role granted on the resource group replacing "
                "the default deployment options gets the options given whole"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.UPDATE)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, Deployed]:
        return ReplacingDeploymentOptions()

    @override
    def then(self) -> Then[AGroupAndACaller, Deployed]:
        return TheDeploymentOptionsAreReplaced()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReplaceTheDeploymentOptions(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Deployed]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-replace-the-default-deployment-options"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 기본 배포 옵션을 교체하려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing trying to replace the default deployment options is "
                "rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, Deployed]:
        return ReplacingDeploymentOptions()

    @override
    def then(self) -> Then[AGroupAndACaller, Deployed]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReplacesTheSessionOptions(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Sessioned]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-replaces-the-default-session-options-whole"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 우선순위와 등록된 처리기 하나의 설정을 담아 기본 세션 옵션을 "
            "교체하면 지정한 옵션 전체가 반환되고 주지 않은 항목은 코드의 기본값입니다",
            english=(
                "when the superadmin replaces the default session options with a priority and "
                "the settings of one registered handler, the options given come back whole and "
                "the entries left out take the defaults in the code"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, Sessioned]:
        return ReplacingSessionOptions()

    @override
    def then(self) -> Then[AGroupAndACaller, Sessioned]:
        return TheSessionOptionsAreReplaced()


@dataclass(frozen=True)
class AnUnregisteredSessionHandlerIsRefused(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Sessioned]
):
    @override
    def summary(self) -> str:
        return "naming-an-unregistered-session-handler-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "등록되지 않은 세션 처리기 이름을 담아 교체하려 하면 잘못된 입력으로 거부됩니다",
            english=(
                "replacing the options with the name of an unregistered session handler is "
                "rejected as invalid input"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, Sessioned]:
        return ReplacingSessionOptions(unregistered=True)

    @override
    def then(self) -> Then[AGroupAndACaller, Sessioned]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReplaceTheSessionOptions(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, Sessioned]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-replace-the-default-session-options"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 기본 세션 옵션을 교체하려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing trying to replace the default session options is "
                "rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, Sessioned]:
        return ReplacingSessionOptions()

    @override
    def then(self) -> Then[AGroupAndACaller, Sessioned]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[OptionsStep] = [
    TheSuperadminReplacesTheDeploymentOptions(),
    AnUnregisteredDeploymentHandlerIsRefused(),
    AUserGrantedUpdateReplacesTheDeploymentOptions(),
    AUserGrantedNothingMayNotReplaceTheDeploymentOptions(),
    TheSuperadminReplacesTheSessionOptions(),
    AnUnregisteredSessionHandlerIsRefused(),
    AUserGrantedNothingMayNotReplaceTheSessionOptions(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_options(
    scenario: OptionsStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
