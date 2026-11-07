"""리비전 상태 전이: 승인, 거절, 가져오기 취소, 정리, 가져오기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.artifact.response import ArtifactRevisionNode
from ai.backend.common.dto.manager.v2.artifact.types import ArtifactStatus as DtoStatus
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.data.artifact.types import ArtifactStatus as DataStatus
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.artifact import (
    ArtifactRevisionDeletionBadRequestError,
    ArtifactRevisionNotVerified,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.artifact import (
    AnArtifactWithRevisionsAndACaller,
    AnArtifactWithRevisionsAndSomeone,
    ManyArtifactsWithRevisionsAndACaller,
    ManyArtifactsWithRevisionsAndSomeone,
    TheRevisionNode,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class Approving(When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]):
    @override
    def operation(self) -> str:
        return "approve_revision"

    @override
    def describe(self, laid: AnArtifactWithRevisionsAndACaller) -> str:
        version = laid.revisions[0].version
        return Says(
            f"{laid.caller.username}이 리비전 {version}을 승인합니다",
            english=f"{laid.caller.username} approves revision {version}",
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactWithRevisionsAndACaller
    ) -> ArtifactRevisionNode:
        with ActingAs(laid.caller):
            return await adapter.approve_revision(laid.revisions[0].id)


@dataclass(frozen=True)
class Rejecting(When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]):
    @override
    def operation(self) -> str:
        return "reject_revision"

    @override
    def describe(self, laid: AnArtifactWithRevisionsAndACaller) -> str:
        version = laid.revisions[0].version
        return Says(
            f"{laid.caller.username}이 리비전 {version}을 거절합니다",
            english=f"{laid.caller.username} rejects revision {version}",
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactWithRevisionsAndACaller
    ) -> ArtifactRevisionNode:
        with ActingAs(laid.caller):
            return await adapter.reject_revision(laid.revisions[0].id)


@dataclass(frozen=True)
class CancellingTheImport(
    When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]
):
    @override
    def operation(self) -> str:
        return "cancel_import"

    @override
    def describe(self, laid: AnArtifactWithRevisionsAndACaller) -> str:
        version = laid.revisions[0].version
        return Says(
            f"{laid.caller.username}이 리비전 {version}의 가져오기를 취소합니다",
            english=f"{laid.caller.username} cancels the import of revision {version}",
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactWithRevisionsAndACaller
    ) -> ArtifactRevisionNode:
        with ActingAs(laid.caller):
            return await adapter.cancel_import(laid.revisions[0].id)


@dataclass(frozen=True)
class CleaningUp(When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]):
    @override
    def operation(self) -> str:
        return "cleanup_revision"

    @override
    def describe(self, laid: AnArtifactWithRevisionsAndACaller) -> str:
        version = laid.revisions[0].version
        return Says(
            f"{laid.caller.username}이 리비전 {version}을 정리합니다",
            english=f"{laid.caller.username} cleans up revision {version}",
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactWithRevisionsAndACaller
    ) -> ArtifactRevisionNode:
        with ActingAs(laid.caller):
            return await adapter.cleanup_revision(laid.revisions[0].id)


@dataclass(frozen=True)
class Importing(
    When[
        AnArtifactWithRevisionsAndACaller, ArtifactAdapter, tuple[ArtifactRevisionNode, UUID | None]
    ]
):
    @override
    def operation(self) -> str:
        return "import_revision"

    @override
    def describe(self, laid: AnArtifactWithRevisionsAndACaller) -> str:
        version = laid.revisions[0].version
        return Says(
            f"{laid.caller.username}이 리비전 {version}을 가져옵니다",
            english=f"{laid.caller.username} imports revision {version}",
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: AnArtifactWithRevisionsAndACaller
    ) -> tuple[ArtifactRevisionNode, UUID | None]:
        with ActingAs(laid.caller):
            return await adapter.import_revision(laid.revisions[0].id, None, None, False)


@dataclass(frozen=True)
class DelegatingTheImport(
    When[
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[list[ArtifactRevisionNode], list[UUID | None]],
    ]
):
    @override
    def operation(self) -> str:
        return "delegate_import_batch"

    @override
    def describe(self, laid: ManyArtifactsWithRevisionsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 리비전 둘의 가져오기를 다른 레지스트리에 위임합니다",
            english=(
                f"{laid.caller.username} delegates the import of two revisions to another registry"
            ),
        )

    @override
    async def call(
        self, adapter: ArtifactAdapter, laid: ManyArtifactsWithRevisionsAndACaller
    ) -> tuple[list[ArtifactRevisionNode], list[UUID | None]]:
        with ActingAs(laid.caller):
            return await adapter.delegate_import_batch(
                None,
                None,
                None,
                [one.revisions[0].id for one in laid.laid],
                False,
            )


@dataclass(frozen=True)
class ApprovingVerifiesTheRevision(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "approving-a-revision-waiting-for-approval-makes-it-available"

    @override
    def describe(self) -> str:
        return Says(
            "승인 대기 중인 리비전을 승인하면, 사용 가능 상태의 리비전이 옵니다",
            english=(
                "when a revision waiting for approval is approved, the revision comes back in "
                "the available state"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ, Permission.UPDATE),
            revisions=(("1.0", DataStatus.NEEDS_APPROVAL),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return Approving()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheRevisionNode(status=DtoStatus.AVAILABLE)


@dataclass(frozen=True)
class ARevisionNotWaitingIsNotApproved(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-revision-not-waiting-for-approval-is-not-approved"

    @override
    def describe(self) -> str:
        return Says(
            "승인 대기 상태가 아닌 리비전은 승인할 수 없고, 검증되지 않았다는 것으로 거부됩니다",
            english=(
                "a revision that is not waiting for approval cannot be approved, and it is "
                "rejected as not verified"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ, Permission.UPDATE),
            revisions=(("1.0", DataStatus.SCANNED),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return Approving()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheCallIsRefused(ArtifactRevisionNotVerified)


@dataclass(frozen=True)
class AUserGrantedReadButNotUpdateMayNotApprove(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-but-not-update-may-not-approve-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 권한만 받은 사용자가 리비전을 승인하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read permission tries to approve a revision, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ,),
            revisions=(("1.0", DataStatus.NEEDS_APPROVAL),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return Approving()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class RejectingMakesItRejected(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "rejecting-an-available-revision-makes-it-rejected"

    @override
    def describe(self) -> str:
        return Says(
            "사용 가능한 리비전을 거절하면, 거절됨 상태의 리비전이 옵니다. 거절은 상태를 가리지 "
            "않습니다",
            english=(
                "when an available revision is rejected, the revision comes back in the rejected "
                "state. Rejecting does not check the status it starts from"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ, Permission.UPDATE),
            revisions=(("1.0", DataStatus.AVAILABLE),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return Rejecting()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheRevisionNode(status=DtoStatus.REJECTED)


@dataclass(frozen=True)
class AUserGrantedReadButNotUpdateMayNotReject(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-but-not-update-may-not-reject-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 권한만 받은 사용자가 리비전을 거절하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read permission tries to reject a revision, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ,),
            revisions=(("1.0", DataStatus.AVAILABLE),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return Rejecting()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class CancellingARunningImportMakesItScanned(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "cancelling-a-running-import-puts-the-revision-back-to-scanned"

    @override
    def describe(self) -> str:
        return Says(
            "가져오는 중인 리비전의 가져오기를 취소하면, 스캔됨 상태의 리비전이 옵니다",
            english=(
                "when the import of a revision that is being pulled is cancelled, the revision "
                "comes back in the scanned state"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ, Permission.UPDATE),
            revisions=(("1.0", DataStatus.PULLING),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return CancellingTheImport()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheRevisionNode(status=DtoStatus.SCANNED)


@dataclass(frozen=True)
class AUserGrantedReadButNotUpdateMayNotCancelAnImport(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-but-not-update-may-not-cancel-an-import"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 권한만 받은 사용자가 리비전의 가져오기를 취소하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read permission tries to cancel the import of a "
                "revision, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ,),
            revisions=(("1.0", DataStatus.PULLING),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return CancellingTheImport()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class CleaningUpARevisionStillBeingScannedIsRefused(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "cleaning-up-a-scanned-revision-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "스캔만 된 리비전은 정리할 수 없고, 정리할 준비가 되지 않았다는 것으로 거부됩니다",
            english=(
                "a revision that has only been scanned cannot be cleaned up, and it is rejected "
                "as not ready to be cleaned up"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ, Permission.SOFT_DELETE),
            revisions=(("1.0", DataStatus.SCANNED),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return CleaningUp()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheCallIsRefused(ArtifactRevisionDeletionBadRequestError)


@dataclass(frozen=True)
class AUserGrantedReadButNotSoftDeleteMayNotCleanUp(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        ArtifactRevisionNode,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-but-not-soft-delete-may-not-clean-up-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 권한만 받은 사용자가 리비전을 정리하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read permission tries to clean up a revision, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ,),
            revisions=(("1.0", DataStatus.AVAILABLE),),
        )

    @override
    def when(
        self,
    ) -> When[AnArtifactWithRevisionsAndACaller, ArtifactAdapter, ArtifactRevisionNode]:
        return CleaningUp()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, ArtifactRevisionNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ImportingWithoutReservoirConfiguredIsRefused(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[ArtifactRevisionNode, UUID | None],
    ]
):
    @override
    def summary(self) -> str:
        return "importing-without-reservoir-configuration-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "Reservoir 설정 없이 리비전을 가져오려 하면, 서버가 설정되지 않았다는 것으로 "
            "거부됩니다",
            english=(
                "when a revision is imported without reservoir configuration, it is rejected as "
                "the server being misconfigured"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER, granted=(Permission.READ, Permission.CREATE)
        )

    @override
    def when(
        self,
    ) -> When[
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[ArtifactRevisionNode, UUID | None],
    ]:
        return Importing()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, tuple[ArtifactRevisionNode, UUID | None]]:
        return TheCallIsRefused(ServerMisconfiguredError)


@dataclass(frozen=True)
class AUserGrantedReadButNotCreateMayNotImport(
    Scenario[
        TestSeedingSession,
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[ArtifactRevisionNode, UUID | None],
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-but-not-create-may-not-import-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 권한만 받은 사용자가 리비전을 가져오려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read permission tries to import a revision, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AnArtifactWithRevisionsAndACaller]:
        return AnArtifactWithRevisionsAndSomeone(
            role=UserRole.USER,
            granted=(Permission.READ,),
            revisions=(("1.0", DataStatus.SCANNED),),
        )

    @override
    def when(
        self,
    ) -> When[
        AnArtifactWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[ArtifactRevisionNode, UUID | None],
    ]:
        return Importing()

    @override
    def then(
        self,
    ) -> Then[AnArtifactWithRevisionsAndACaller, tuple[ArtifactRevisionNode, UUID | None]]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class DelegatingTheImportWithoutReservoirConfiguredIsRefused(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[list[ArtifactRevisionNode], list[UUID | None]],
    ]
):
    @override
    def summary(self) -> str:
        return "delegating-an-import-without-reservoir-configuration-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "Reservoir 설정 없이 가져오기를 위임하려 하면, 서버가 설정되지 않았다는 것으로 "
            "거부됩니다",
            english=(
                "when an import is delegated without reservoir configuration, it is rejected as "
                "the server being misconfigured"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(
            role=UserRole.SUPERADMIN, revisions=(("1.0", DataStatus.SCANNED),)
        )

    @override
    def when(
        self,
    ) -> When[
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[list[ArtifactRevisionNode], list[UUID | None]],
    ]:
        return DelegatingTheImport()

    @override
    def then(
        self,
    ) -> Then[
        ManyArtifactsWithRevisionsAndACaller,
        tuple[list[ArtifactRevisionNode], list[UUID | None]],
    ]:
        return TheCallIsRefused(ServerMisconfiguredError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelegateAnImport(
    Scenario[
        TestSeedingSession,
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[list[ArtifactRevisionNode], list[UUID | None]],
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delegate-an-import"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 가져오기를 위임하려 하면, 전역 역할이 없어 권한 "
            "부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to delegate an import, it is rejected for lack "
                "of permission because they hold no global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyArtifactsWithRevisionsAndACaller]:
        return ManyArtifactsWithRevisionsAndSomeone(
            role=UserRole.USER, revisions=(("1.0", DataStatus.SCANNED),)
        )

    @override
    def when(
        self,
    ) -> When[
        ManyArtifactsWithRevisionsAndACaller,
        ArtifactAdapter,
        tuple[list[ArtifactRevisionNode], list[UUID | None]],
    ]:
        return DelegatingTheImport()

    @override
    def then(
        self,
    ) -> Then[
        ManyArtifactsWithRevisionsAndACaller,
        tuple[list[ArtifactRevisionNode], list[UUID | None]],
    ]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Scenario[TestSeedingSession, Any, ArtifactAdapter, Any]] = [
    ApprovingVerifiesTheRevision(),
    ARevisionNotWaitingIsNotApproved(),
    AUserGrantedReadButNotUpdateMayNotApprove(),
    RejectingMakesItRejected(),
    AUserGrantedReadButNotUpdateMayNotReject(),
    CancellingARunningImportMakesItScanned(),
    AUserGrantedReadButNotUpdateMayNotCancelAnImport(),
    CleaningUpARevisionStillBeingScannedIsRefused(),
    AUserGrantedReadButNotSoftDeleteMayNotCleanUp(),
    ImportingWithoutReservoirConfiguredIsRefused(),
    AUserGrantedReadButNotCreateMayNotImport(),
    DelegatingTheImportWithoutReservoirConfiguredIsRefused(),
    AUserGrantedNothingMayNotDelegateAnImport(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_revision_transitions(
    scenario: Scenario[TestSeedingSession, Any, ArtifactAdapter, Any],
    adapter: ArtifactAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
