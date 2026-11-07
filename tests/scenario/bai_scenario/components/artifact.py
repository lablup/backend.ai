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

from ai.backend.common.data.entity.artifact import ArtifactEntityType
from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.response import (
    AdminSearchArtifactRevisionsPayload,
    AdminSearchArtifactsPayload,
    ArtifactNode,
    ArtifactRevisionNode,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactRegistryType,
    ArtifactType,
)
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactStatus as DtoArtifactStatus,
)
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactRevisionData,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactStatus as DataArtifactStatus,
)
from ai.backend.manager.data.artifact.types import (
    ArtifactType as DataArtifactType,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
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
    Says,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import Mentions, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.artifact.artifact import TestSeedArtifact
from bai_scenario.seeds.artifact.revision import TestSeedArtifactRevision
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest

WAS_HERE = Says("이미 있던 아티팩트", english="an artifact that already existed")
"""시드가 미리 만드는 아티팩트의 설명. 시나리오가 기대값으로 다시 쓰므로 한 자리에 둔다."""


def _holding(role: UserRole, granted: tuple[Permission, ...]) -> Says:
    """호출자가 아티팩트에 무엇을 할 수 있는지 한 줄로."""
    who = role.value
    if role is UserRole.SUPERADMIN:
        return Says(f"{who} 한 명", english=f"one {who}")
    if not granted:
        return Says(
            f"아무 권한도 받지 않은 {who} 한 명",
            english=f"one {who} with no permission",
        )
    names = ", ".join(str(permission.name) for permission in granted)
    return Says(
        f"아티팩트에 {names} 권한을 받은 {who} 한 명",
        english=f"one {who} granted {names} on artifacts",
    )


@dataclass(frozen=True)
class SomeoneGrantedOnArtifacts(TestSeedNest[Laid[UserData]]):
    """그 사용자에게 global 에서 아티팩트에 대한 권한을 준다."""

    domain: Laid[Any]
    granted: tuple[Permission, ...]
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return Says(
            "global 에서 아티팩트 권한을 받은 사용자 준비",
            english="Prepare a user granted permission on artifacts in global",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.GLOBAL), name_hint="artifact-keeper"
            ),
            someone,
        )
        for permission in self.granted:
            seed.adding(
                TestSeedPermission(entity_type=ArtifactEntityType(), permission=permission),
                role,
            )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def _lay_caller(
    seeding: Any, domain: Laid[Any], role: UserRole, granted: tuple[Permission, ...]
) -> Laid[UserData]:
    """The caller a row asks for, with the permissions the row names."""
    caller: Laid[UserData]
    if not granted:
        caller = await seeding.within(SomeoneOf(domain, role=role))
    else:
        caller = await seeding.within(SomeoneGrantedOnArtifacts(domain, granted, role=role))
    return caller


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
    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        holding = _holding(self.role, self.granted)
        return Says(
            f"아티팩트 하나와, {holding}",
            english=f"one artifact and {holding.english}",
        )

    @override
    async def lay(self, seeding: Any) -> AnArtifactAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home"))
        artifact = await seeding.creating(TestSeedArtifact(description=WAS_HERE))
        caller = await _lay_caller(seeding, domain, self.role, self.granted)
        return AnArtifactAndACaller(seeding.made(artifact), seeding.made(caller))


@dataclass(frozen=True)
class ManyArtifactsAndSomeone(Given[Any, ManyArtifactsAndACaller]):
    """아티팩트 여럿과 사용자 한 명."""

    role: UserRole = UserRole.USER
    granted: tuple[Permission, ...] = ()
    count: int = 2

    @override
    def describe(self) -> str:
        holding = _holding(self.role, self.granted)
        return Says(
            f"아티팩트 {self.count}개와, {holding}",
            english=f"{self.count} artifacts and {holding.english}",
        )

    @override
    async def lay(self, seeding: Any) -> ManyArtifactsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home"))
        artifacts = [
            await seeding.creating(TestSeedArtifact(description=WAS_HERE))
            for _ in range(self.count)
        ]
        caller = await _lay_caller(seeding, domain, self.role, self.granted)
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
            Same(f"{prefix}type", node.type, ArtifactType(laid.type.value)),
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
            Held[UUID](
                f"{prefix}id",
                node.id,
                SameAs(
                    laid.id,
                    Says(
                        "미리 저장한 아티팩트의 id",
                        english="the id of the artifact made in advance",
                    ),
                ),
            ),
            Held[UUID](
                f"{prefix}entity_id",
                node.entity_id,
                SameAs(
                    laid.id,
                    Says(
                        "미리 저장한 아티팩트의 id",
                        english="the id of the artifact made in advance",
                    ),
                ),
            ),
            Held[UUID](
                f"{prefix}registry_id",
                node.registry_id,
                SameAs(
                    laid.registry_id,
                    Says(
                        "미리 저장한 아티팩트의 레지스트리 id",
                        english="the registry id of the artifact made in advance",
                    ),
                ),
            ),
            Held[UUID](
                f"{prefix}source_registry_id",
                node.source_registry_id,
                SameAs(
                    laid.source_registry_id,
                    Says(
                        "미리 저장한 아티팩트의 레지스트리 id",
                        english="the registry id of the artifact made in advance",
                    ),
                ),
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
        return Says(
            "미리 저장한 아티팩트 전체가 반환됩니다",
            english="the whole artifact made in advance comes back",
        )

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
            return Says(
                "대상 아티팩트가 모두 처리된 모습으로 오고, 실패한 것은 없습니다",
                english="every target artifact comes back processed, and none failed",
            )
        return Says(
            "대상 아티팩트가 모두 처리된 모습으로 오고, 없는 id 는 대상이 없다는 이유로 "
            "실패 목록에 옵니다",
            english=(
                "every target artifact comes back processed, and the missing id comes back "
                "in the failed list with a reason that it does not exist"
            ),
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
class NothingIsProcessed(Then[ManyArtifactsAndACaller, PartialBulkPayload[ArtifactNode]]):
    """처리된 아티팩트 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 아티팩트 없이 대상이 모두 실패 목록에 옵니다",
            english="no artifact is processed and every target comes back in the failed list",
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
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, artifact) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        artifact.id,
                        Says(
                            "대상 아티팩트의 id",
                            english="the id of the target artifact",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class AnArtifactWithRevisionsAndACaller:
    """아티팩트 하나와 그 리비전들, 그리고 그것을 부를 사람."""

    artifact: ArtifactData
    revisions: tuple[ArtifactRevisionData, ...]
    caller: UserData


@dataclass(frozen=True)
class ArtifactWithItsRevisions:
    """아티팩트 하나와, 그 아티팩트가 가진 리비전들."""

    artifact: ArtifactData
    revisions: tuple[ArtifactRevisionData, ...]


@dataclass(frozen=True)
class ManyArtifactsWithRevisionsAndACaller:
    """리비전을 가진 아티팩트 여럿과, 그것들을 부를 사람."""

    laid: tuple[ArtifactWithItsRevisions, ...]
    caller: UserData


@dataclass(frozen=True)
class AnArtifactWithRevisionsAndSomeone(Given[Any, AnArtifactWithRevisionsAndACaller]):
    """아티팩트 하나와 리비전 여럿, 사용자 한 명."""

    role: UserRole = UserRole.SUPERADMIN
    granted: tuple[Permission, ...] = ()
    revisions: tuple[tuple[str, DataArtifactStatus], ...] = (("1.0", DataArtifactStatus.SCANNED),)

    @override
    def describe(self) -> str:
        holding = _holding(self.role, self.granted)
        return Says(
            f"아티팩트 하나와 리비전 {len(self.revisions)}개, 그리고 {holding}",
            english=(f"one artifact with {len(self.revisions)} revisions and {holding.english}"),
        )

    @override
    async def lay(self, seeding: Any) -> AnArtifactWithRevisionsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home"))
        artifact = await seeding.creating(TestSeedArtifact(description=WAS_HERE))
        revisions = [
            await seeding.adding(TestSeedArtifactRevision(version=version, status=status), artifact)
            for version, status in self.revisions
        ]
        caller = await _lay_caller(seeding, domain, self.role, self.granted)
        return AnArtifactWithRevisionsAndACaller(
            artifact=seeding.made(artifact),
            revisions=tuple(seeding.made(one) for one in revisions),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ManyArtifactsWithRevisionsAndSomeone(Given[Any, ManyArtifactsWithRevisionsAndACaller]):
    """리비전을 가진 아티팩트 여럿과 사용자 한 명. 아티팩트마다 같은 리비전을 갖는다."""

    role: UserRole = UserRole.SUPERADMIN
    granted: tuple[Permission, ...] = ()
    count: int = 2
    revisions: tuple[tuple[str, DataArtifactStatus], ...] = (
        ("1.0", DataArtifactStatus.SCANNED),
        ("2.0", DataArtifactStatus.NEEDS_APPROVAL),
    )

    @override
    def describe(self) -> str:
        holding = _holding(self.role, self.granted)
        return Says(
            f"리비전 {len(self.revisions)}개를 가진 아티팩트 {self.count}개와, {holding}",
            english=(
                f"{self.count} artifacts with {len(self.revisions)} revisions each and "
                f"{holding.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyArtifactsWithRevisionsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home"))
        laid: list[ArtifactWithItsRevisions] = []
        for _ in range(self.count):
            artifact = await seeding.creating(TestSeedArtifact(description=WAS_HERE))
            revisions = [
                await seeding.adding(
                    TestSeedArtifactRevision(version=version, status=status), artifact
                )
                for version, status in self.revisions
            ]
            laid.append(
                ArtifactWithItsRevisions(
                    artifact=seeding.made(artifact),
                    revisions=tuple(seeding.made(one) for one in revisions),
                )
            )
        caller = await _lay_caller(seeding, domain, self.role, self.granted)
        return ManyArtifactsWithRevisionsAndACaller(laid=tuple(laid), caller=seeding.made(caller))


@dataclass(frozen=True)
class ArtifactsToSearch:
    """검색할 아티팩트들과, 그중 이름으로 골라낼 하나, 그리고 부를 사람."""

    laid: tuple[ArtifactData, ...]
    named: ArtifactData
    models: tuple[ArtifactData, ...]
    packages: tuple[ArtifactData, ...]
    caller: UserData


@dataclass(frozen=True)
class ArtifactsWorthSearching(Given[Any, ArtifactsToSearch]):
    """모델 아티팩트 여럿과 패키지 아티팩트 하나, 사용자 한 명."""

    role: UserRole = UserRole.SUPERADMIN
    granted: tuple[Permission, ...] = ()
    models: int = 2
    packages: int = 1

    @override
    def describe(self) -> str:
        holding = _holding(self.role, self.granted)
        return Says(
            f"모델 아티팩트 {self.models}개와 패키지 아티팩트 {self.packages}개, 그리고 {holding}",
            english=(
                f"{self.models} model artifacts and {self.packages} package artifacts, and "
                f"{holding.english}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ArtifactsToSearch:
        domain = await seeding.creating(TestSeedDomain(name_hint="home"))
        models = [
            await seeding.creating(
                TestSeedArtifact(description=WAS_HERE, type=DataArtifactType.MODEL)
            )
            for _ in range(self.models)
        ]
        packages = [
            await seeding.creating(
                TestSeedArtifact(description=WAS_HERE, type=DataArtifactType.PACKAGE)
            )
            for _ in range(self.packages)
        ]
        caller = await _lay_caller(seeding, domain, self.role, self.granted)
        modelled = tuple(seeding.made(one) for one in models)
        return ArtifactsToSearch(
            laid=tuple(seeding.made(one) for one in [*models, *packages]),
            named=modelled[0],
            models=modelled,
            packages=tuple(seeding.made(one) for one in packages),
            caller=seeding.made(caller),
        )


def revision_verdicts(
    prefix: str,
    node: ArtifactRevisionNode,
    artifact: ArtifactData,
    revision: ArtifactRevisionData,
    status: DtoArtifactStatus | None = None,
) -> list[Verdict]:
    """Every place of one revision node, prefixed for a node inside a list."""
    return [
        Held[UUID](
            f"{prefix}id",
            node.id,
            SameAs(
                revision.id,
                Says(
                    "미리 저장한 리비전의 id",
                    english="the id of the revision created in advance",
                ),
            ),
        ),
        Held[UUID](
            f"{prefix}field_id",
            node.field_id,
            SameAs(
                revision.id,
                Says(
                    "미리 저장한 리비전의 id",
                    english="the id of the revision created in advance",
                ),
            ),
        ),
        Held[UUID](
            f"{prefix}artifact_id",
            node.artifact_id,
            SameAs(
                artifact.id,
                Says(
                    "미리 저장한 아티팩트의 id",
                    english="the id of the artifact created in advance",
                ),
            ),
        ),
        Same(f"{prefix}version", node.version, revision.version),
        Same(
            f"{prefix}size",
            node.size,
            str(revision.size) if revision.size is not None else None,
        ),
        Same(
            f"{prefix}status",
            node.status,
            status if status is not None else DtoArtifactStatus(revision.status.value),
        ),
        Same(
            f"{prefix}remote_status",
            node.remote_status,
            revision.remote_status.value if revision.remote_status is not None else None,
        ),
        Same(f"{prefix}created_at", node.created_at, revision.created_at),
        Same(f"{prefix}updated_at", node.updated_at, revision.updated_at),
        Skipped(
            f"{prefix}digest",
            Says(
                "어댑터가 리비전 노드에 다이제스트를 담지 않아 응답으로 확인할 수 없습니다",
                english=(
                    "the adapter does not put the digest on the revision node, so it cannot be "
                    "stated from the response"
                ),
            ),
        ),
        Skipped(
            f"{prefix}verification_result",
            Says(
                "어댑터가 검증 결과를 리비전 노드에 담지 않아 응답으로 확인할 수 없습니다",
                english=(
                    "the adapter does not put the verification result on the revision node, so it "
                    "cannot be stated from the response"
                ),
            ),
        ),
        Same(f"{prefix}readme", node.readme, revision.readme),
    ]


@dataclass(frozen=True)
class TheRevisionNode(Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]):
    """리비전 노드 하나가 통째로 온다."""

    index: int = 0
    status: DtoArtifactStatus | None = None

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 리비전 전체가 반환됩니다",
            english="the whole revision created in advance comes back",
        )

    @override
    def look(
        self, laid: AnArtifactWithRevisionsAndACaller, answered: Answered[ArtifactRevisionNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return revision_verdicts("", node, laid.artifact, laid.revisions[self.index], self.status)


@dataclass(frozen=True)
class TheArtifactPage(Then[ArtifactsToSearch, AdminSearchArtifactsPayload]):
    """검색 결과 한 페이지가 통째로 온다.

    ``ordered_by_name`` 이면 이름 오름차순으로 온 순서를 그대로 견주고, 아니면 id 순서로 맞춰
    견준다. ``limit`` 은 한 페이지에 담기는 개수다.
    """

    started: datetime
    only_models: bool = False
    ordered_by_name: bool = False
    limit: int | None = None

    @override
    def says(self) -> str:
        if self.only_models:
            return Says(
                "모델 아티팩트만 이름 순서로 한 페이지에 옵니다",
                english="only model artifacts come back, in name order on one page",
            )
        return Says(
            "미리 저장한 아티팩트가 모두 한 페이지로 옵니다",
            english="every artifact made in advance comes back on one page",
        )

    @override
    def look(
        self, laid: ArtifactsToSearch, answered: Answered[AdminSearchArtifactsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        matched = [
            one for one in laid.laid if not self.only_models or one.type is DataArtifactType.MODEL
        ]
        if self.ordered_by_name:
            matched.sort(key=lambda artifact: artifact.name)
        expected = matched if self.limit is None else matched[: self.limit]
        answered_in_order = list(payload.items)
        laid_in_order = list(expected)
        if not self.ordered_by_name:
            answered_in_order.sort(key=lambda node: node.id)
            laid_in_order.sort(key=lambda artifact: artifact.id)
        verdicts: list[Verdict] = [
            Same("count", len(payload.items), len(expected)),
            Same("total_count", payload.total_count, len(matched)),
            Same(
                "has_next_page",
                payload.has_next_page,
                self.limit is not None and len(matched) > len(expected),
            ),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for i, (node, artifact) in enumerate(zip(answered_in_order, laid_in_order, strict=False)):
            verdicts += ArtifactLook().verdicts(f"[{i}].", node, artifact, self.started)
        return verdicts


@dataclass(frozen=True)
class TheRevisionPage(
    Then[ManyArtifactsWithRevisionsAndACaller, AdminSearchArtifactRevisionsPayload]
):
    """검색 결과 한 페이지가 통째로 온다.

    ``ordered_by_version`` 이면 버전 오름차순으로 온 순서를 그대로 견주고, 아니면 id 순서로
    맞춰 견준다. ``limit`` 은 한 페이지에 담기는 개수다.
    """

    only_status: DataArtifactStatus | None = None
    only_artifact_index: int | None = None
    ordered_by_version: bool = False
    limit: int | None = None

    @override
    def says(self) -> str:
        if self.only_status is not None:
            return Says(
                "그 상태의 리비전만 버전 순서로 한 페이지에 옵니다",
                english=("only revisions in that status come back, in version order on one page"),
            )
        if self.only_artifact_index is not None:
            return Says(
                "그 아티팩트가 가진 리비전만 한 페이지로 옵니다",
                english="only the revisions the artifact holds come back on one page",
            )
        return Says(
            "미리 저장한 리비전이 모두 한 페이지로 옵니다",
            english="every revision made in advance comes back on one page",
        )

    def matched(
        self, laid: ManyArtifactsWithRevisionsAndACaller
    ) -> tuple[tuple[ArtifactData, ArtifactRevisionData], ...]:
        artifacts = (
            laid.laid
            if self.only_artifact_index is None
            else (laid.laid[self.only_artifact_index],)
        )
        pairs = [(one.artifact, revision) for one in artifacts for revision in one.revisions]
        if self.only_status is None:
            return tuple(pairs)
        return tuple(pair for pair in pairs if pair[1].status is self.only_status)

    @override
    def look(
        self,
        laid: ManyArtifactsWithRevisionsAndACaller,
        answered: Answered[AdminSearchArtifactRevisionsPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        matched = list(self.matched(laid))
        if self.ordered_by_version:
            matched.sort(key=lambda pair: (pair[1].version, pair[1].id))
        expected = matched if self.limit is None else matched[: self.limit]
        answered_in_order = list(payload.items)
        laid_in_order = list(expected)
        if not self.ordered_by_version:
            answered_in_order.sort(key=lambda node: node.id)
            laid_in_order.sort(key=lambda pair: pair[1].id)
        verdicts: list[Verdict] = [
            Same("count", len(payload.items), len(expected)),
            Same("total_count", payload.total_count, len(matched)),
            Same(
                "has_next_page",
                payload.has_next_page,
                self.limit is not None and len(matched) > len(expected),
            ),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for i, (node, (artifact, revision)) in enumerate(
            zip(answered_in_order, laid_in_order, strict=False)
        ):
            verdicts += revision_verdicts(f"[{i}].", node, artifact, revision)
        return verdicts
