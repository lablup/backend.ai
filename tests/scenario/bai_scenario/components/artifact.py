"""What an artifact scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds what is left: the types an artifact table is
written against, and the situations worth naming more than once.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactRegistryType,
    ArtifactType,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.artifact import ArtifactNotFoundError
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
from bai_scenario.components.domain import Mentions, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.artifact.artifact import TestSeedArtifact
from bai_scenario.seeds.domain.domain import TestSeedDomain

WAS_HERE = "이미 있던 아티팩트"
"""시드가 미리 만드는 아티팩트의 설명. 시나리오가 기대값으로 다시 쓰므로 한 자리에 둔다."""


@dataclass(frozen=True)
class AnArtifactAndACaller:
    """아티팩트 하나와, 그것을 부를 사람."""

    artifact: ArtifactData
    caller: UserData


@dataclass(frozen=True)
class ManyArtifactsAndACaller:
    """아티팩트 여럿과, 그것들을 부를 사람."""

    laid: tuple[ArtifactData, ...]
    caller: UserData


@dataclass(frozen=True)
class AnArtifactAndSomeone(Given[Any, AnArtifactAndACaller]):
    """아티팩트 하나와 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"아티팩트 하나와 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> AnArtifactAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home"))
        artifact = await seeding.creating(TestSeedArtifact(description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return AnArtifactAndACaller(seeding.made(artifact), seeding.made(caller))


@dataclass(frozen=True)
class ManyArtifactsAndSomeone(Given[Any, ManyArtifactsAndACaller]):
    """아티팩트 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return f"아티팩트 {self.count}개와 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyArtifactsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home"))
        artifacts = [
            await seeding.creating(TestSeedArtifact(description=WAS_HERE))
            for _ in range(self.count)
        ]
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ManyArtifactsAndACaller(
            laid=tuple(seeding.made(one) for one in artifacts),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ArtifactLook:
    """미리 만든 아티팩트의 노드가 어떤 값으로 와야 하는지. 이름은 미리 만든 것에서 읽는다."""

    described: str | None = WAS_HERE
    availability: ArtifactAvailability = ArtifactAvailability.ALIVE
    readonly: bool = False

    def verdicts(
        self, prefix: str, node: ArtifactNode, laid: ArtifactData, started: datetime
    ) -> list[Verdict]:
        return [
            Same(f"{prefix}name", node.name, laid.name),
            Same(f"{prefix}type", node.type, ArtifactType.MODEL),
            Same(f"{prefix}description", node.description, self.described),
            Same(f"{prefix}registry_type", node.registry_type, ArtifactRegistryType.HUGGINGFACE),
            Same(
                f"{prefix}source_registry_type",
                node.source_registry_type,
                ArtifactRegistryType.HUGGINGFACE,
            ),
            Same(f"{prefix}availability", node.availability, self.availability),
            Same(f"{prefix}readonly", node.readonly, self.readonly),
            Same(f"{prefix}extra", node.extra, None),
            Same(f"{prefix}revisions", node.revisions, []),
            Held[UUID](f"{prefix}id", node.id, SameAs(laid.id, "미리 만든 아티팩트의 id")),
            Held[UUID](
                f"{prefix}entity_id", node.entity_id, SameAs(laid.id, "미리 만든 아티팩트의 id")
            ),
            Held[UUID](
                f"{prefix}registry_id",
                node.registry_id,
                SameAs(laid.registry_id, "미리 만든 아티팩트의 레지스트리 id"),
            ),
            Held[UUID](
                f"{prefix}source_registry_id",
                node.source_registry_id,
                SameAs(laid.source_registry_id, "미리 만든 아티팩트의 레지스트리 id"),
            ),
            Held(f"{prefix}scanned_at", node.scanned_at, WrittenByThisRun(started)),
            Held(f"{prefix}updated_at", node.updated_at, WrittenByThisRun(started)),
        ]


@dataclass(frozen=True)
class TheArtifactNode(Then[AnArtifactAndACaller, ArtifactNode]):
    """아티팩트 노드 하나가 통째로 온다. 답이 노드를 감싸고 있으면 `when`이 벗겨서 준다."""

    started: datetime
    expected: ArtifactLook = ArtifactLook()

    @override
    def says(self) -> str:
        return "미리 만든 아티팩트 전체가 온다"

    @override
    def look(self, laid: AnArtifactAndACaller, answered: Answered[ArtifactNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(ArtifactNotFoundError, answered.raised)]
        return self.expected.verdicts("", node, laid.artifact, self.started)


@dataclass(frozen=True)
class EveryTargetComesBack(Then[ManyArtifactsAndACaller, PartialBulkPayload[ArtifactNode]]):
    """대상이 모두 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    expected: ArtifactLook
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return "대상 아티팩트가 모두 처리된 모습으로 오고, 실패한 것은 없다"
        return (
            "대상 아티팩트가 모두 처리된 모습으로 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 온다"
        )

    @override
    def look(
        self,
        laid: ManyArtifactsAndACaller,
        answered: Answered[PartialBulkPayload[ArtifactNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, artifact) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += self.expected.verdicts(f"successes[{i}].", node, artifact, self.started)
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
class NothingIsProcessed(Then[ManyArtifactsAndACaller, PartialBulkPayload[ArtifactNode]]):
    """처리된 아티팩트 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 아티팩트 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: ManyArtifactsAndACaller,
        answered: Answered[PartialBulkPayload[ArtifactNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, artifact) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id", failure.id, SameAs(artifact.id, "대상 아티팩트의 id")
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
