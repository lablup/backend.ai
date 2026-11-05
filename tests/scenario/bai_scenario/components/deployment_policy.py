"""What a deployment policy scenario table says besides the call.

A policy is a field row of a deployment, so a caller reaches it through the deployment's
permissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.dto.manager.v2.deployment.response import DeploymentPolicyNode
from ai.backend.common.dto.manager.v2.deployment.types import BlueGreenStrategySpecInfo
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentPolicyData,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Verdict,
)
from bai_scenario.components.deployment import lay_a_deployment, lay_a_place
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.seeds.deployment.policy import TestSeedDeploymentPolicyOf

POLICY_ID = Says(
    "미리 저장한 정책의 id", english="the id of the policy seeded in advance"
)
STRATEGY = Says(
    "미리 저장한 정책의 전략", english="the strategy of the policy seeded in advance"
)


@dataclass(frozen=True)
class ThePolicyNode:
    """미리 저장한 정책의 노드가 어떤 값으로 와야 하는지. 값은 심은 것에서 읽는다."""

    started: datetime

    def verdicts(        self, node: DeploymentPolicyNode, laid: DeploymentPolicyData, at: str = ""
    ) -> list[Verdict]:
        spec = node.strategy_spec
        spec_verdicts: list[Verdict] = [
            Held(
                f"{at}strategy_spec.strategy",
                spec.strategy,
                SameAs(laid.strategy, STRATEGY),
            )
        ]
        if isinstance(spec, BlueGreenStrategySpecInfo):
            bg = _as_bg(laid)
            spec_verdicts += [
                Same(f"{at}strategy_spec.auto_promote", spec.auto_promote, bg.auto_promote),
                Same(
                    f"{at}strategy_spec.promote_delay_seconds",
                    spec.promote_delay_seconds,
                    bg.promote_delay_seconds,
                ),
            ]
        else:
            rolling = _as_rolling(laid)
            spec_verdicts += [
                Same(f"{at}strategy_spec.max_surge", spec.max_surge, rolling.max_surge),
                Same(
                    f"{at}strategy_spec.max_unavailable",
                    spec.max_unavailable,
                    rolling.max_unavailable,
                ),
            ]
        return [
            Held[UUID](f"{at}id", node.id, SameAs(laid.id, POLICY_ID)),
            Held[UUID](f"{at}field_id", node.field_id, SameAs(laid.id, POLICY_ID)),
            Held[UUID](
                f"{at}deployment_id",
                node.deployment_id,
                SameAs(
                    laid.endpoint,
                    Says("정책이 걸린 배포의 id", english="the id of the deployment the policy sets"),
                ),
            ),
            *spec_verdicts,
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self.started)),
            Held(f"{at}updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


def _as_rolling(laid: DeploymentPolicyData) -> RollingUpdateSpec:
    if isinstance(laid.strategy_spec, RollingUpdateSpec):
        return laid.strategy_spec
    raise ValueError(f"expected a rolling-update spec, got {type(laid.strategy_spec).__name__}")


def _as_bg(laid: DeploymentPolicyData) -> BlueGreenSpec:
    if isinstance(laid.strategy_spec, BlueGreenSpec):
        return laid.strategy_spec
    raise ValueError(f"expected a blue-green spec, got {type(laid.strategy_spec).__name__}")


@dataclass(frozen=True)
class APolicyOfADeploymentAndACaller:
    """배포 하나와 걸린 정책 하나, 그것을 부를 사람."""

    deployment: DeploymentInfo
    policy: DeploymentPolicyData
    caller: UserData


@dataclass(frozen=True)
class APolicyAndACaller(Given[Any, APolicyOfADeploymentAndACaller]):
    """정책 하나가 걸린 배포 하나와, 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        if self.role is UserRole.SUPERADMIN:
            who_ko = "superadmin"
            who_en = "the superadmin"
        elif not self.granted:
            who_ko = "아무 배포 권한도 받지 않은 사용자"
            who_en = "a user with no deployment permission"
        else:
            names = ", ".join(p.name or "" for p in self.granted)
            who_ko = f"배포에 {names} 권한을 받은 사용자"
            who_en = f"a user granted the {names} permission on deployments"
        return Says(
            f"정책 하나가 걸린 배포 하나와, {who_ko} 한 명",
            english=f"one deployment holding one policy, and {who_en}",
        )

    @override
    async def lay(self, seeding: Any) -> APolicyOfADeploymentAndACaller:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        deployment = await lay_a_deployment(seeding, place)
        policy = await seeding.adding(TestSeedDeploymentPolicyOf(), deployment)
        return APolicyOfADeploymentAndACaller(
            deployment=seeding.made(deployment),
            policy=seeding.made(policy),
            caller=seeding.made(place.caller),
        )
