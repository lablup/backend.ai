"""자동 스케일링 규칙 여럿 수정하기, purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import (
    PartialBulkPurgeAutoScalingRulesInput,
    PartialBulkUpdateAutoScalingRulesInput,
    UpdateAutoScalingRuleInput,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment.response import AutoScalingRuleNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.auto_scaling_rule import (
    LAID_METRIC,
    EveryRuleComesBack,
    NoRuleIsProcessed,
    RulesOfADeployment,
    RulesOfADeploymentAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "memory_util"

type Answer = PartialBulkPayload[AutoScalingRuleNode]
type RuleStep = Scenario[
    TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class EditingEveryRule(When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """규칙들의 지표 이름을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update_rules"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        return f"{laid.caller.username}이 규칙 {len(laid.rules)}개의 지표 이름을 한 번에 고침"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update_rules(
                PartialBulkUpdateAutoScalingRulesInput(
                    items=[
                        UpdateAutoScalingRuleInput(id=rule.id, metric_name=EDITED)
                        for rule in laid.rules
                    ]
                )
            )


@dataclass(frozen=True)
class PurgingEveryRule(When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """규칙들을 한 번에 purge 한다. ``missing``이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge_rules"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 규칙 {len(laid.rules)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller) -> Answer:
        ids: list[UUID] = [rule.id for rule in laid.rules]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge_rules(
                PartialBulkPurgeAutoScalingRulesInput(ids=ids)
            )


@dataclass(frozen=True)
class AnEditorEditsSeveralRules(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-deployment-editor-edits-several-rules-at-once"

    @override
    def describe(self) -> str:
        return (
            "배포 수정 권한을 받은 사용자가 규칙 여럿의 지표 이름을 한 번에 바꾸면, 모두 새 "
            "이름으로 오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return EditingEveryRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return EveryRuleComesBack(metric_name=EDITED)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-rules"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 규칙 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return EditingEveryRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return NoRuleIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class PurgingAnswersForTheMissingRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-rules-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "배포 영구 삭제 권한을 받은 사용자가 규칙 둘과 없는 id 하나를 한 번에 purge 하면, "
            "둘은 purge 되기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return PurgingEveryRule(missing=self.missing)

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return EveryRuleComesBack(metric_name=LAID_METRIC, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-rules"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 규칙 여럿을 한 번에 purge 하려 하면, purge 된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return PurgingEveryRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return NoRuleIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class AnEditorPurgesNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-deployment-editor-purges-none-of-several-rules"

    @override
    def describe(self) -> str:
        return (
            "배포 수정 권한만 받은 사용자가 규칙 여럿을 한 번에 purge 하려 하면, purge 된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return PurgingEveryRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return NoRuleIsProcessed(reason="Insufficient permission")


SCENARIOS: list[RuleStep] = [
    AnEditorEditsSeveralRules(),
    AUserGrantedNothingEditsNoRule(),
    PurgingAnswersForTheMissingRule(),
    AUserGrantedNothingPurgesNoRule(),
    AnEditorPurgesNoRule(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_auto_scaling_rules(
    scenario: RuleStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
