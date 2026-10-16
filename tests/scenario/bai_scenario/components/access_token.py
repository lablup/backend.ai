"""What an access token scenario table says besides the call.

A token is a field row of a deployment, so a caller reaches it through the deployment's
permissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment.response import AccessTokenNode
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    ModelDeploymentAccessTokenData,
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
from bai_scenario.seeds.deployment.access_token import TestSeedAccessTokenOf


@dataclass(frozen=True)
class TokensOfADeploymentAndACaller:
    """배포 하나에 걸린 접근 토큰 여럿과, 그것을 부를 사람."""

    deployment: DeploymentInfo
    tokens: tuple[ModelDeploymentAccessTokenData, ...]
    caller: UserData


@dataclass(frozen=True)
class TokensOfADeployment(Given[Any, TokensOfADeploymentAndACaller]):
    """접근 토큰 여럿이 걸린 배포 하나와, 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    count: int = 2

    @override
    def describe(self) -> str:
        who = (
            "아무 배포 권한도 받지 않은 사용자"
            if not self.granted
            else f"배포에 {', '.join(p.name or '' for p in self.granted)} 권한을 받은 사용자"
        )
        return f"접근 토큰 {self.count}개가 걸린 배포 하나와, {who} 한 명"

    @override
    async def lay(self, seeding: Any) -> TokensOfADeploymentAndACaller:
        place = await lay_a_place(seeding, granted=self.granted)
        deployment = await lay_a_deployment(seeding, place)
        domain = seeding.made(place.domain)
        project = seeding.made(place.project)
        caller = seeding.made(place.caller)
        tokens = [
            await seeding.adding(
                TestSeedAccessTokenOf(
                    domain=domain.name,
                    project_id=ProjectID(project.id),
                    session_owner_id=UserID(caller.id),
                ),
                deployment,
            )
            for _ in range(self.count)
        ]
        return TokensOfADeploymentAndACaller(
            deployment=seeding.made(deployment),
            tokens=tuple(seeding.made(token) for token in tokens),
            caller=caller,
        )


@dataclass(frozen=True)
class EveryTokenComesBack(Then[TokensOfADeploymentAndACaller, PartialBulkPayload[AccessTokenNode]]):
    """토큰이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return "토큰이 모두 처리된 목록에 오고, 실패한 것은 없다"
        return "토큰이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"

    @override
    def look(
        self,
        laid: TokensOfADeploymentAndACaller,
        answered: Answered[PartialBulkPayload[AccessTokenNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.tokens))
        ]
        for i, (node, token) in enumerate(zip(payload.successes, laid.tokens, strict=False)):
            verdicts.append(
                Held[UUID](f"successes[{i}].id", node.id, SameAs(token.id, "심은 토큰의 id"))
            )
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
class NoTokenIsProcessed(Then[TokensOfADeploymentAndACaller, PartialBulkPayload[AccessTokenNode]]):
    """처리된 토큰 없이, 토큰이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 토큰 없이 토큰이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: TokensOfADeploymentAndACaller,
        answered: Answered[PartialBulkPayload[AccessTokenNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.tokens)),
        ]
        for i, (failure, token) in enumerate(zip(payload.failed, laid.tokens, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(token.id, "심은 토큰의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
