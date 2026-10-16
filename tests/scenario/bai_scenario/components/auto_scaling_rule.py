"""What an auto-scaling rule scenario table says besides the call.

A rule is a field row of a deployment, so a caller reaches it through the deployment's
permissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment.response import AutoScalingRuleNode
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)
from bai_scenario.components.deployment import lay_a_deployment, lay_a_place
from bai_scenario.components.domain import Mentions
from bai_scenario.seeds.deployment.auto_scaling_rule import TestSeedAutoScalingRuleOf

LAID_METRIC = "cpu_util"


@dataclass(frozen=True)
class RulesOfADeploymentAndACaller:
    """배포 하나에 걸린 규칙 여럿과, 그것을 부를 사람."""

    deployment: DeploymentInfo
    rules: tuple[ModelDeploymentAutoScalingRuleData, ...]
    caller: UserData


@dataclass(frozen=True)
class RulesOfADeployment(Given[Any, RulesOfADeploymentAndACaller]):
    """규칙 여럿이 걸린 배포 하나와, 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    count: int = 2

    @override
    def describe(self) -> str:
        who = (
            "아무 배포 권한도 받지 않은 사용자"
            if not self.granted
            else f"배포에 {', '.join(p.name or '' for p in self.granted)} 권한을 받은 사용자"
        )
        return f"자동 스케일링 규칙 {self.count}개가 걸린 배포 하나와, {who} 한 명"

    @override
    async def lay(self, seeding: Any) -> RulesOfADeploymentAndACaller:
        place = await lay_a_place(seeding, granted=self.granted)
        deployment = await lay_a_deployment(seeding, place)
        rules = [
            await seeding.adding(TestSeedAutoScalingRuleOf(metric_name=LAID_METRIC), deployment)
            for _ in range(self.count)
        ]
        return RulesOfADeploymentAndACaller(
            deployment=seeding.made(deployment),
            rules=tuple(seeding.made(rule) for rule in rules),
            caller=seeding.made(place.caller),
        )


@dataclass(frozen=True)
class EveryRuleComesBack(
    Then[RulesOfADeploymentAndACaller, PartialBulkPayload[AutoScalingRuleNode]]
):
    """규칙이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    metric_name: str
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return f"규칙이 모두 지표 이름 '{self.metric_name}'으로 오고, 실패한 것은 없다"
        return (
            f"규칙이 모두 지표 이름 '{self.metric_name}'으로 오고, 없는 id 는 대상이 없다는 "
            "이유로 실패 목록에 온다"
        )

    @override
    def look(
        self,
        laid: RulesOfADeploymentAndACaller,
        answered: Answered[PartialBulkPayload[AutoScalingRuleNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.rules))]
        for i, (node, rule) in enumerate(zip(payload.successes, laid.rules, strict=False)):
            verdicts += [
                Held[UUID](f"successes[{i}].id", node.id, SameAs(rule.id, "심은 규칙의 id")),
                Same(f"successes[{i}].metric_name", node.metric_name, self.metric_name),
            ]
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NoRuleIsProcessed(
    Then[RulesOfADeploymentAndACaller, PartialBulkPayload[AutoScalingRuleNode]]
):
    """처리된 규칙 없이, 규칙이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 규칙 없이 규칙이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: RulesOfADeploymentAndACaller,
        answered: Answered[PartialBulkPayload[AutoScalingRuleNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.rules)),
        ]
        for i, (failure, rule) in enumerate(zip(payload.failed, laid.rules, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(rule.id, "심은 규칙의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
