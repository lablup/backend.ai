"""What an access token scenario table says besides the call.

A token is a field row of a deployment, so a caller reaches it through the deployment's
permissions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
    Says,
    Then,
    Verdict,
)
from bai_scenario.components.deployment import lay_a_deployment, lay_a_place
from bai_scenario.components.domain import Mentions, WrittenByThisRun
from bai_scenario.seeds.deployment.access_token import TestSeedAccessTokenOf

TOKEN_ID = Says(
    "미리 저장한 토큰의 id", english="the id of the token seeded in advance"
)


@dataclass(frozen=True)
class TheTokenNode:
    """미리 저장한 토큰의 노드가 어떤 값으로 와야 하는지. 값은 심은 것에서 읽는다."""

    started: datetime

    def verdicts(
        self, node: AccessTokenNode, laid: ModelDeploymentAccessTokenData, at: str = ""
    ) -> list[Verdict]:
        return [
            Held[UUID](f"{at}id", node.id, SameAs(laid.id, TOKEN_ID)),
            Held[UUID](f"{at}field_id", node.field_id, SameAs(laid.id, TOKEN_ID)),
            Same(f"{at}token", node.token, laid.token),
            Same(f"{at}expires_at", node.expires_at, laid.expires_at),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self.started)),
        ]


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
        if not self.granted:
            who_ko = "아무 배포 권한도 받지 않은 사용자"
            who_en = "a user with no deployment permission"
        else:
            names = ", ".join(p.name or "" for p in self.granted)
            who_ko = f"배포에 {names} 권한을 받은 사용자"
            who_en = f"a user granted the {names} permission on deployments"
        return Says(
            f"접근 토큰 {self.count}개가 걸린 배포 하나와, {who_ko} 한 명",
            english=f"one deployment holding {self.count} access tokens, and {who_en}",
        )

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
            return Says(
                "토큰이 모두 처리된 목록에 오고, 실패한 것은 없습니다",
                english="every token comes back in the processed list, and none failed",
            )
        return Says(
            "토큰이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "every token comes back in the processed list, and the missing id comes back "
                "in the failed list with a reason that it does not exist"
            ),
        )

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
                Held[UUID](
                    f"successes[{i}].id",
                    node.id,
                    SameAs(
                        token.id,
                        Says(
                            "미리 저장한 토큰의 id",
                            english="the id of the token seeded in advance",
                        ),
                    ),
                )
            )
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
class NoTokenIsProcessed(Then[TokensOfADeploymentAndACaller, PartialBulkPayload[AccessTokenNode]]):
    """처리된 토큰 없이, 토큰이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 토큰 없이 토큰이 모두 실패 목록에 옵니다",
            english="no token is processed and every token comes back in the failed list",
        )

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
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        token.id,
                        Says(
                            "미리 저장한 토큰의 id",
                            english="the id of the token seeded in advance",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
