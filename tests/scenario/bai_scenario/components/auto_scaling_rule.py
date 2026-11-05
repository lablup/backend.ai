"""What an auto-scaling rule scenario table says besides the call.

A rule is a field row of a deployment, so a caller reaches it through the deployment's
permissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
    Says,
    Then,
    Verdict,
)
from bai_scenario.components.deployment import lay_a_deployment, lay_a_place
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.seeds.deployment.auto_scaling_rule import TestSeedAutoScalingRuleOf

LAID_METRIC = "cpu_util"

RULE_ID = Says(
    "미리 저장한 규칙의 id", english="the id of the rule seeded in advance"
)


@dataclass(frozen=True)
class TheRuleNode:
    """미리 저장한 규칙의 노드가 어떤 값으로 와야 하는지. 값은 심은 것에서 읽는다."""

    started: datetime

    def verdicts(
        self, node: AutoScalingRuleNode, laid: ModelDeploymentAutoScalingRuleData, at: str = ""
    ) -> list[Verdict]:
        return [
            Held[UUID](f"{at}id", node.id, SameAs(laid.id, RULE_ID)),
            Held[UUID](f"{at}field_id", node.field_id, SameAs(laid.id, RULE_ID)),
            Held[UUID](
                f"{at}deployment_id",
                node.deployment_id,
                SameAs(
                    laid.model_deployment_id,
                    Says("규칙이 걸린 배포의 id", english="the id of the deployment the rule scales"),
                ),
            ),
            Same(f"{at}metric_source", node.metric_source, laid.metric_source.name),
            Same(f"{at}metric_name", node.metric_name, laid.metric_name),
            Same(f"{at}min_threshold", node.min_threshold, laid.min_threshold),
            Same(f"{at}max_threshold", node.max_threshold, laid.max_threshold),
            Same(f"{at}step_size", node.step_size, laid.step_size),
            Same(f"{at}time_window", node.time_window, laid.time_window),
            Same(f"{at}min_replicas", node.min_replicas, laid.min_replicas),
            Same(f"{at}max_replicas", node.max_replicas, laid.max_replicas),
            Same(
                f"{at}prometheus_query_preset_id",
                node.prometheus_query_preset_id,
                laid.prometheus_query_preset_id,
            ),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self.started)),
            Same(f"{at}last_triggered_at", node.last_triggered_at, laid.last_triggered_at),
        ]


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
        if not self.granted:
            who_ko = "아무 배포 권한도 받지 않은 사용자"
            who_en = "a user with no deployment permission"
        else:
            names = ", ".join(p.name or "" for p in self.granted)
            who_ko = f"배포에 {names} 권한을 받은 사용자"
            who_en = f"a user granted the {names} permission on deployments"
        return Says(
            f"자동 스케일링 규칙 {self.count}개가 걸린 배포 하나와, {who_ko} 한 명",
            english=f"one deployment holding {self.count} auto-scaling rules, and {who_en}",
        )

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
            return Says(
                f"규칙이 모두 지표 이름 '{self.metric_name}'으로 오고, 실패한 것은 없습니다",
                english=(
                    f"every rule comes back with metric name '{self.metric_name}', and none failed"
                ),
            )
        return Says(
            f"규칙이 모두 지표 이름 '{self.metric_name}'으로 오고, 없는 id 는 대상이 없다는 "
            "이유로 실패 목록에 옵니다",
            english=(
                f"every rule comes back with metric name '{self.metric_name}', and the "
                "missing id comes back in the failed list with a reason that it does not exist"
            ),
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
                Held[UUID](
                    f"successes[{i}].id",
                    node.id,
                    SameAs(
                        rule.id,
                        Says(
                            "미리 저장한 규칙의 id",
                            english="the id of the rule seeded in advance",
                        ),
                    ),
                ),
                Same(f"successes[{i}].metric_name", node.metric_name, self.metric_name),
            ]
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says(
                            "요청에 넣은 없는 id",
                            english="the nonexistent id sent in the request",
                        ),
                    ),
                ),
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
        return Says(
            "처리된 규칙 없이 규칙이 모두 실패 목록에 옵니다",
            english="no rule is processed and every rule comes back in the failed list",
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
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.rules)),
        ]
        for i, (failure, rule) in enumerate(zip(payload.failed, laid.rules, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        rule.id,
                        Says(
                            "미리 저장한 규칙의 id",
                            english="the id of the rule seeded in advance",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
