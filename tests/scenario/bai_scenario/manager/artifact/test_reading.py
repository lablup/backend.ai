"""아티팩트 하나와 리비전 하나를 id 로 읽기, 그리고 id 목록으로 한 번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactNode, ArtifactRevisionNode
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.data.artifact.types import ArtifactStatus as DataStatus
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.artifact import (
    AnArtifactAndACaller,
    AnArtifactAndSomeone,
    AnArtifactNode,
    AnArtifactRevisionNode,
    AnArtifactWithRevisionsAndACaller,
    AnArtifactWithRevisionsAndSomeone,
    ArtifactLook,
    ManyArtifactsAndACaller,
    ManyArtifactsAndSomeone,
    ManyArtifactsWithRevisionsAndACaller,
    ManyArtifactsWithRevisionsAndSomeone,
    TheArtifactNode,
    TheRevisionNode,
    revision_verdicts,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID(int=1)
"""어떤 행도 가리키지 않는 id."""

type LoadedArtifacts = list[ArtifactNode | Exception | None]
type LoadedRevisions = list[ArtifactRevisionNode | Exception | None]
type ScenarioStep = Scenario[TestSeedingSession, Any, ArtifactAdapter, Any]


@dataclass(frozen=True)
class Getting(When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]):
    """미리 저장한 아티팩트를 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: AnArtifactAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.artifact.name}을 id 로 읽습니다",
            english=f"{laid.caller.username} reads {laid.artifact.name} by id",
        )

    @override
    async def call(self, adapter: ArtifactAdapter, laid: AnArtifactAndACaller) -> ArtifactNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.artifact.id)


@dataclass(frozen=True)
class ReadingTheRevision(
    When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]
):
    """미리 저장한 리비전 하나를 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get_revision"

    @override
    def describe(self, laid: AnArtifactWithRevisionsAndACaller) -> str:
        version = laid.revisions[0].version
        return Says(
            f"{laid.caller.username}이 {laid.artifact.name}의 리비전 {version}을 id 로 읽습니다",
            english=(
                f"{laid.caller.username} reads revision {version} of {laid.artifact.name} by id"
            ),
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactWithRevisionsAndACaller
    ) -> ArtifactRevisionNode:
        with ActingAs(laid.caller):
            return await adapter.get_revision(laid.revisions[0].id)


@dataclass(frozen=True)
class LoadingArtifacts(When[ManyArtifactsAndACaller, ArtifactAdapter, LoadedArtifacts]):
    """미리 저장한 아티팩트 둘을 한 번에 읽는다. ``include_missing`` 이면 없는 id 하나를 끼운다."""

    empty: bool = False
    include_missing: bool = True

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ManyArtifactsAndACaller) -> str:
        who = laid.caller.username
        if self.empty:
            return Says(
                f"{who}이 빈 id 목록으로 읽습니다",
                english=f"{who} loads with an empty id list",
            )
        if self.include_missing:
            return Says(
                f"{who}이 미리 저장한 아티팩트 {len(laid.laid)}개와 없는 id 하나를 한 번에 읽습니다",
                english=(
                    f"{who} loads {len(laid.laid)} artifacts made in advance and one id that does "
                    "not exist at once"
                ),
            )
        return Says(
            f"{who}이 미리 저장한 아티팩트 {len(laid.laid)}개를 한 번에 읽습니다",
            english=f"{who} loads {len(laid.laid)} artifacts made in advance at once",
        )

    def ids(self, laid: ManyArtifactsAndACaller) -> list[UUID]:
        if self.empty:
            return []
        if self.include_missing:
            return [laid.laid[0].id, MISSING, laid.laid[1].id]
        return [laid.laid[0].id, laid.laid[1].id]

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: ManyArtifactsAndACaller
    ) -> LoadedArtifacts:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids(self.ids(laid))


@dataclass(frozen=True)
class LoadingRevisions(
    When[ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, LoadedRevisions]
):
    """아티팩트마다 하나씩 있는 리비전 둘을 한 번에 읽는다. ``include_missing`` 이면 없는 id 하나를 끼운다."""

    empty: bool = False
    include_missing: bool = True

    @override
    def operation(self) -> str:
        return "batch_load_revisions_by_ids"

    @override
    def describe(self, laid: ManyArtifactsWithRevisionsAndACaller) -> str:
        who = laid.caller.username
        if self.empty:
            return Says(
                f"{who}이 빈 id 목록으로 읽습니다",
                english=f"{who} loads with an empty id list",
            )
        if self.include_missing:
            return Says(
                f"{who}이 미리 저장한 리비전 둘과 없는 id 하나를 한 번에 읽습니다",
                english=(
                    f"{who} loads two revisions made in advance and one id that does not exist "
                    "at once"
                ),
            )
        return Says(
            f"{who}이 미리 저장한 리비전 둘을 한 번에 읽습니다",
            english=f"{who} loads two revisions made in advance at once",
        )

    def ids(self, laid: ManyArtifactsWithRevisionsAndACaller) -> list[ArtifactRevisionID]:
        if self.empty:
            return []
        if self.include_missing:
            return [
                laid.laid[0].revisions[0].id,
                ArtifactRevisionID(MISSING),
                laid.laid[1].revisions[0].id,
            ]
        return [laid.laid[0].revisions[0].id, laid.laid[1].revisions[0].id]

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: ManyArtifactsWithRevisionsAndACaller
    ) -> LoadedRevisions:
        with ActingAs(laid.caller):
            return await adapter.batch_load_revisions_by_ids(self.ids(laid))


@dataclass(frozen=True)
class TheLoadedArtifacts(Then[ManyArtifactsAndACaller, LoadedArtifacts]):
    """자리마다 아티팩트 노드가 요청한 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자리마다 미리 저장한 아티팩트 전체가 요청한 순서대로 옵니다",
            english="every position holds a whole artifact made in advance, in the requested order",
        )

    @override
    def look(
        self, laid: ManyArtifactsAndACaller, answered: Answered[LoadedArtifacts]
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(got), len(laid.laid))]
        if len(got) != len(laid.laid):
            return verdicts
        for i, (one, artifact) in enumerate(zip(got, laid.laid, strict=False)):
            if isinstance(one, ArtifactNode):
                verdicts += ArtifactLook().verdicts(f"[{i}].", one, artifact, self.started)
            else:
                verdicts.append(Held(f"[{i}].artifact", one, AnArtifactNode()))
        return verdicts


@dataclass(frozen=True)
class TheLoadedRevisions(Then[ManyArtifactsWithRevisionsAndACaller, LoadedRevisions]):
    """자리마다 리비전 노드가 요청한 순서대로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "자리마다 미리 저장한 리비전 전체가 요청한 순서대로 옵니다",
            english="every position holds a whole revision made in advance, in the requested order",
        )

    @override
    def look(
        self,
        laid: ManyArtifactsWithRevisionsAndACaller,
        answered: Answered[LoadedRevisions],
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        entries = [(one.artifact, one.revisions[0]) for one in laid.laid]
        verdicts: list[Verdict] = [Same("length", len(got), len(entries))]
        if len(got) != len(entries):
            return verdicts
        for i, (one, (artifact, revision)) in enumerate(zip(got, entries, strict=False)):
            if isinstance(one, ArtifactRevisionNode):
                verdicts += revision_verdicts(f"[{i}].", one, artifact, revision)
            else:
                verdicts.append(Held(f"[{i}].revision", one, AnArtifactRevisionNode()))
        return verdicts


@dataclass(frozen=True)
class EveryArtifactPositionIsRefused(Then[ManyArtifactsAndACaller, LoadedArtifacts]):
    """읽을 수 없는 id 자리마다 거부가 담긴다. 없는 id 와 구별되지 않는다."""

    @override
    def says(self) -> str:
        return Says(
            "자리마다 권한 부족 거부가 담겨 오고, 없는 id 도 같은 거부로 와서 있는지 없는지가 "
            "드러나지 않습니다",
            english=(
                "every position holds a rejection for lack of permission, and the id that does "
                "not exist comes back with the same rejection, so whether it exists is not "
                "revealed"
            ),
        )

    @override
    def look(
        self, laid: ManyArtifactsAndACaller, answered: Answered[LoadedArtifacts]
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("length", len(got), 3),
            *[
                Refused(NotEnoughPermission, one if isinstance(one, Exception) else None)
                for one in got
            ],
        ]


@dataclass(frozen=True)
class EveryUnreadableRevisionIsRefused(Then[ManyArtifactsWithRevisionsAndACaller, LoadedRevisions]):
    """읽을 수 없는 리비전 자리마다 거부가 담긴다. 없는 id 자리는 확인하지 않는다."""

    @override
    def says(self) -> str:
        return Says(
            "읽을 수 없는 리비전 자리마다 권한 부족 거부가 담깁니다",
            english=(
                "every revision the caller may not read comes back with a rejection for lack of "
                "permission"
            ),
        )

    @override
    def look(
        self,
        laid: ManyArtifactsWithRevisionsAndACaller,
        answered: Answered[LoadedRevisions],
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if len(got) != 3:
            return [Same("length", len(got), 3)]
        first, _missing, second = got
        return [
            Same("length", len(got), 3),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
            Skipped(
                "[1]",
                Says(
                    "없는 id 는 빈 값으로 오지만 읽을 수 없는 리비전은 거부로 와서, 이 자리가 "
                    "리비전의 존재 여부를 드러냅니다. 결함 후보로 기록하고 기대값으로 굳히지 "
                    "않습니다",
                    english=(
                        "an id naming no revision comes back empty while a revision the caller "
                        "may not read comes back as a denial, so this position reveals whether "
                        "the revision exists. It is recorded as a defect candidate rather than "
                        "pinned as the expected behavior"
                    ),
                ),
            ),
            Refused(NotEnoughPermission, second if isinstance(second, Exception) else None),
        ]


@dataclass(frozen=True)
class AnEmptyListComesBack(Then[ManyArtifactsAndACaller, LoadedArtifacts]):
    @override
    def says(self) -> str:
        return Says("빈 응답이 반환됩니다", english="an empty answer comes back")

    @override
    def look(
        self, laid: ManyArtifactsAndACaller, answered: Answered[LoadedArtifacts]
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class AnEmptyRevisionListComesBack(Then[ManyArtifactsWithRevisionsAndACaller, LoadedRevisions]):
    @override
    def says(self) -> str:
        return Says("빈 응답이 반환됩니다", english="an empty answer comes back")

    @override
    def look(
        self,
        laid: ManyArtifactsWithRevisionsAndACaller,
        answered: Answered[LoadedRevisions],
    ) -> list[Verdict]:
        got = answered.response
        if got is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("items", got, [])]


@dataclass(frozen=True)
class AUserGrantedReadGetsAnArtifact(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-gets-an-artifact"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 읽기 권한을 받은 사용자가 아티팩트를 id 로 읽으면, 미리 저장한 "
            "아티팩트 전체가 옵니다",
            english=(
                "when a user granted read permission on artifacts in global reads an artifact "
                "by id, the whole artifact made in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return Getting()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheArtifactNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotGet(
    Scenario[TestSeedingSession, AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-get-an-artifact"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 아티팩트를 id 로 읽으려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to read an artifact by id, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactAndACaller]:
        return AnArtifactAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[AnArtifactAndACaller, ArtifactAdapter, ArtifactNode]:
        return Getting()

    @override
    def then(self) -> Then[AnArtifactAndACaller, ArtifactNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedReadGetsARevision(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-gets-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 읽기 권한을 받은 사용자가 리비전을 id 로 읽으면, 미리 저장한 "
            "리비전 전체가 옵니다",
            english=(
                "when a user granted read permission on artifacts in global reads a revision by "
                "id, the whole revision made in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return ReadingTheRevision()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheRevisionNode()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadARevision(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 리비전을 id 로 읽으려 하면, 그 리비전을 가진 "
            "아티팩트를 찾을 수 없다는 것으로 거부됩니다",
            english=(
                "when a user granted nothing tries to read a revision by id, it is rejected as "
                "the artifact holding it not being resolvable"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return ReadingTheRevision()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class LoadingKeepsThePositions(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, LoadedArtifacts]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "loading-many-artifact-ids-keeps-the-positions"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 읽기 권한을 받은 사용자가 미리 저장한 아티팩트 둘을 한 번에 "
            "읽으면, 자리마다 미리 저장한 아티팩트 전체가 요청한 순서대로 옵니다",
            english=(
                "when a user granted read permission on artifacts in global loads the two "
                "artifacts made in advance at once, every position holds a whole artifact made "
                "in advance in the requested order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, LoadedArtifacts]:
        return LoadingArtifacts(include_missing=False)

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, LoadedArtifacts]:
        return TheLoadedArtifacts(started=self.started)


@dataclass(frozen=True)
class AnEmptyArtifactListAsksNothing(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, LoadedArtifacts]
):
    @override
    def summary(self) -> str:
        return "an-empty-artifact-id-list-answers-empty"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록으로 아티팩트를 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다",
            english=(
                "loading artifacts with an empty id list calls no lower layer and an empty "
                "answer comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.USER, granted=(Permission.READ,))

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, LoadedArtifacts]:
        return LoadingArtifacts(empty=True)

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, LoadedArtifacts]:
        return AnEmptyListComesBack()


@dataclass(frozen=True)
class APlainUserIsRefusedOnEveryArtifactPosition(
    Scenario[TestSeedingSession, ManyArtifactsAndACaller, ArtifactAdapter, LoadedArtifacts]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-loading-artifacts-is-refused-on-every-position"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 아티팩트 id 여럿을 한 번에 읽으면, 항목마다 권한 부족 "
            "거부가 담겨 오고 없는 id 도 같은 거부로 와서 있는지 없는지가 드러나지 않습니다",
            english=(
                "when a user granted nothing loads several artifact ids at once, every position "
                "holds a rejection for lack of permission, and the id that does not exist comes "
                "back with the same rejection so whether it exists is not revealed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsAndACaller]:
        return ManyArtifactsAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyArtifactsAndACaller, ArtifactAdapter, LoadedArtifacts]:
        return LoadingArtifacts()

    @override
    def then(self) -> Then[ManyArtifactsAndACaller, LoadedArtifacts]:
        return EveryArtifactPositionIsRefused()


@dataclass(frozen=True)
class RevisionLoadingKeepsThePositions(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        LoadedRevisions,
    ]
):
    @override
    def summary(self) -> str:
        return "loading-many-revision-ids-keeps-the-positions"

    @override
    def describe(self) -> str:
        return Says(
            "global 에서 아티팩트 읽기 권한을 받은 사용자가 미리 저장한 리비전 둘을 한 번에 "
            "읽으면, 자리마다 미리 저장한 리비전 전체가 요청한 순서대로 옵니다",
            english=(
                "when a user granted read permission on artifacts in global loads the two "
                "revisions made in advance at once, every position holds a whole revision made "
                "in advance in the requested order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ,),
            revisions=(("1.0", DataStatus.SCANNED),),
        )

    @override
    def when(
        self,
    ) -> When[ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, LoadedRevisions]:
        return LoadingRevisions(include_missing=False)

    @override
    def then(self) -> Then[ManyArtifactsWithRevisionsAndACaller, LoadedRevisions]:
        return TheLoadedRevisions()


@dataclass(frozen=True)
class AnEmptyRevisionListAsksNothing(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        LoadedRevisions,
    ]
):
    @override
    def summary(self) -> str:
        return "an-empty-revision-id-list-answers-empty"

    @override
    def describe(self) -> str:
        return Says(
            "빈 id 목록으로 리비전을 읽으면 하위 계층을 호출하지 않고 빈 응답이 반환됩니다",
            english=(
                "loading revisions with an empty id list calls no lower layer and an empty "
                "answer comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ,),
            revisions=(("1.0", DataStatus.SCANNED),),
        )

    @override
    def when(
        self,
    ) -> When[ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, LoadedRevisions]:
        return LoadingRevisions(empty=True)

    @override
    def then(self) -> Then[ManyArtifactsWithRevisionsAndACaller, LoadedRevisions]:
        return AnEmptyRevisionListComesBack()


@dataclass(frozen=True)
class APlainUserIsRefusedOnEveryReadableRevision(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        LoadedRevisions,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-loading-revisions-is-refused-on-every-readable-one"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 리비전 id 여럿을 한 번에 읽으면, 읽을 수 없는 리비전 "
            "자리마다 권한 부족 거부가 담깁니다",
            english=(
                "when a user granted nothing loads several revision ids at once, every revision "
                "the caller may not read comes back with a rejection for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(
            role=UserRole.USER,
            revisions=(("1.0", DataStatus.SCANNED),),
        )

    @override
    def when(
        self,
    ) -> When[ManyArtifactsWithRevisionsAndACaller, ArtifactAdapter, LoadedRevisions]:
        return LoadingRevisions()

    @override
    def then(self) -> Then[ManyArtifactsWithRevisionsAndACaller, LoadedRevisions]:
        return EveryUnreadableRevisionIsRefused()


SCENARIOS: list[ScenarioStep] = [
    AUserGrantedReadGetsAnArtifact(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotGet(),
    AUserGrantedReadGetsARevision(),
    AUserGrantedNothingMayNotReadARevision(),
    LoadingKeepsThePositions(started=datetime.now(UTC)),
    AnEmptyArtifactListAsksNothing(),
    APlainUserIsRefusedOnEveryArtifactPosition(),
    RevisionLoadingKeepsThePositions(),
    AnEmptyRevisionListAsksNothing(),
    APlainUserIsRefusedOnEveryReadableRevision(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ScenarioStep,
    adapter: ArtifactAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
