"""artifact 리비전 객체의 presigned URL 발급."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.object_storage.response import (
    PresignedDownloadURLPayload,
    PresignedUploadURLPayload,
)
from ai.backend.manager.api.adapters.object_storage.adapter import ObjectStorageAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.artifact import ArtifactReadonly, ArtifactRevisionNotApproved
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.errors.object_storage import ObjectStorageOperationNotSupported
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Configured,
    Given,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.system import lay_a_caller
from bai_scenario.fakes.storage_proxy import (
    PRESIGNED_DOWNLOAD_BASE,
    PRESIGNED_UPLOAD_BASE,
    PRESIGNED_UPLOAD_FIELDS,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.artifact.artifact import (
    TestSeedArtifact,
    TestSeedArtifactRevision,
)
from bai_scenario.seeds.object_storage.object_storage import TestSeedObjectStorage
from bai_scenario.seeds.storage_namespace.storage_namespace import (
    TestSeedStorageNamespace,
)

ARCHIVE_STORAGE = "archive-storage"
"""The object storage the reservoir config names as its archive storage."""

BUCKET = "archive-bucket"
"""The namespace registered under the archive storage."""

VERSION = "1.0"
KEY = "model.bin"

RESERVOIR_CONFIG: Mapping[str, Any] = {
    "reservoir.storage_name": ARCHIVE_STORAGE,
    "reservoir.config.storage_type": "object_storage",
    "reservoir.config.bucket_name": BUCKET,
}

RESERVOIR_VFS_CONFIG: Mapping[str, Any] = {
    "reservoir.storage_name": ARCHIVE_STORAGE,
    "reservoir.config.storage_type": "vfs_storage",
    "reservoir.config.subpath": "models",
}


@dataclass(frozen=True)
class ARevisionAndACaller:
    """artifact 리비전 하나와, 그 리비전의 객체 URL 을 발급할 사용자."""

    artifact: ArtifactData
    revision: ArtifactRevisionData
    caller: UserData


@dataclass(frozen=True)
class ARevisionAndSomeone(Given[Any, ARevisionAndACaller]):
    """artifact 하나와 그 리비전 하나, superadmin 한 명."""

    readonly: bool = False
    status: ArtifactStatus = ArtifactStatus.AVAILABLE

    @override
    def describe(self) -> str:
        state_ko = "읽기 전용" if self.readonly else "쓸 수 있는"
        state_en = "readonly" if self.readonly else "writable"
        return Says(
            f"{state_ko} artifact 하나와 그 리비전 하나, superadmin 한 명",
            english=f"one {state_en} artifact and one of its revisions, and one superadmin",
        )

    @override
    async def lay(self, seeding: Any) -> ARevisionAndACaller:
        storage = await seeding.creating(TestSeedObjectStorage(fixed_name=ARCHIVE_STORAGE))
        await seeding.creating_from(TestSeedStorageNamespace(namespace=BUCKET), storage)
        artifact = await seeding.creating(TestSeedArtifact(readonly=self.readonly))
        revision = await seeding.adding(
            TestSeedArtifactRevision(version=VERSION, status=self.status), artifact
        )
        caller = await lay_a_caller(seeding, UserRole.SUPERADMIN)
        return ARevisionAndACaller(
            seeding.made(artifact), seeding.made(revision), seeding.made(caller)
        )


@dataclass(frozen=True)
class Downloading(When[ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload]):
    @override
    def operation(self) -> str:
        return "get_presigned_download_url"

    @override
    def describe(self, laid: ARevisionAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 리비전의 {KEY} 객체를 내려받을 URL 을 요청합니다",
            english=f"{laid.caller.username} asks for a URL to download {KEY} of the revision",
        )

    @override
    async def call(
        self, adapter: ObjectStorageAdapter, laid: ARevisionAndACaller
    ) -> PresignedDownloadURLPayload:
        with ActingAs(laid.caller):
            return await adapter.get_presigned_download_url(laid.revision.id, KEY)


@dataclass(frozen=True)
class Uploading(When[ARevisionAndACaller, ObjectStorageAdapter, PresignedUploadURLPayload]):
    @override
    def operation(self) -> str:
        return "get_presigned_upload_url"

    @override
    def describe(self, laid: ARevisionAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 리비전에 {KEY} 객체를 올릴 URL 을 요청합니다",
            english=f"{laid.caller.username} asks for a URL to upload {KEY} to the revision",
        )

    @override
    async def call(
        self, adapter: ObjectStorageAdapter, laid: ARevisionAndACaller
    ) -> PresignedUploadURLPayload:
        with ActingAs(laid.caller):
            return await adapter.get_presigned_upload_url(laid.revision.id, KEY)


@dataclass(frozen=True)
class TheDownloadUrl(Then[ARevisionAndACaller, PresignedDownloadURLPayload]):
    @override
    def says(self) -> str:
        return Says(
            "그 객체의 저장 경로로 만든 내려받기 URL 이 반환됩니다",
            english="a download URL made from the object's stored path comes back",
        )

    @override
    def look(
        self, laid: ARevisionAndACaller, answered: Answered[PresignedDownloadURLPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        object_path = Path(laid.artifact.name) / laid.revision.version / KEY
        return [
            Same(
                "presigned_url",
                payload.presigned_url,
                f"{PRESIGNED_DOWNLOAD_BASE}/{object_path}",
            )
        ]


@dataclass(frozen=True)
class TheUploadUrl(Then[ARevisionAndACaller, PresignedUploadURLPayload]):
    @override
    def says(self) -> str:
        return Says(
            "그 객체의 저장 경로로 만든 올리기 URL 과 함께 올릴 때 붙일 값이 반환됩니다",
            english=(
                "an upload URL made from the object's stored path comes back with the fields to "
                "send along"
            ),
        )

    @override
    def look(
        self, laid: ARevisionAndACaller, answered: Answered[PresignedUploadURLPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        object_path = Path(laid.artifact.name) / laid.revision.version / KEY
        return [
            Same(
                "presigned_url",
                payload.presigned_url,
                f"{PRESIGNED_UPLOAD_BASE}/{object_path}",
            ),
            Same("fields", json.loads(payload.fields), dict(PRESIGNED_UPLOAD_FIELDS)),
        ]


@dataclass(frozen=True)
class TheSuperadminDownloads(
    Scenario[
        TestSeedingSession, ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "the-superadmin-gets-a-download-url-for-an-available-revision"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 사용 가능한 리비전의 객체를 내려받을 URL 을 요청하면 그 객체의 저장 "
            "경로로 만든 URL 이 반환됩니다",
            english=(
                "when the superadmin asks for a URL to download an object of an available "
                "revision, a URL made from the object's stored path comes back"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return RESERVOIR_CONFIG

    @override
    def given(self) -> Given[TestSeedingSession, ARevisionAndACaller]:
        return ARevisionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload]:
        return Downloading()

    @override
    def then(self) -> Then[ARevisionAndACaller, PresignedDownloadURLPayload]:
        return TheDownloadUrl()


@dataclass(frozen=True)
class AnUnavailableRevisionIsRefused(
    Scenario[
        TestSeedingSession, ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "downloading-an-unavailable-revision-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "사용 가능 상태가 아닌 리비전의 객체를 내려받을 URL 을 요청하면 승인되지 않았다는 "
            "이유로 거부됩니다",
            english=(
                "when a download URL is asked for a revision that is not available, it is "
                "rejected because the revision is not approved"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return RESERVOIR_CONFIG

    @override
    def given(self) -> Given[TestSeedingSession, ARevisionAndACaller]:
        return ARevisionAndSomeone(status=ArtifactStatus.SCANNED)

    @override
    def when(
        self,
    ) -> When[ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload]:
        return Downloading()

    @override
    def then(self) -> Then[ARevisionAndACaller, PresignedDownloadURLPayload]:
        return TheCallIsRefused(ArtifactRevisionNotApproved)


@dataclass(frozen=True)
class NoReservoirConfigIsRefused(
    Scenario[
        TestSeedingSession, ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload
    ],
):
    @override
    def summary(self) -> str:
        return "downloading-with-no-reservoir-config-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "전역 설정에 reservoir 가 없으면 내려받기 URL 을 요청해도 발급되지 않고 서버 설정이 "
            "잘못됐다는 이유로 거부됩니다",
            english=(
                "when the global config has no reservoir, a download URL request is rejected "
                "because the server is misconfigured"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARevisionAndACaller]:
        return ARevisionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload]:
        return Downloading()

    @override
    def then(self) -> Then[ARevisionAndACaller, PresignedDownloadURLPayload]:
        return TheCallIsRefused(ServerMisconfiguredError)


@dataclass(frozen=True)
class AVfsReservoirIsRefused(
    Scenario[
        TestSeedingSession, ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "downloading-from-a-vfs-reservoir-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "전역 설정의 reservoir 가 오브젝트 스토리지가 아니면 내려받기 URL 을 요청해도 "
            "발급되지 않고 지원하지 않는 저장소라는 이유로 거부됩니다",
            english=(
                "when the reservoir in the global config is not an object storage, a download "
                "URL request is rejected because the storage is not supported"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return RESERVOIR_VFS_CONFIG

    @override
    def given(self) -> Given[TestSeedingSession, ARevisionAndACaller]:
        return ARevisionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ARevisionAndACaller, ObjectStorageAdapter, PresignedDownloadURLPayload]:
        return Downloading()

    @override
    def then(self) -> Then[ARevisionAndACaller, PresignedDownloadURLPayload]:
        return TheCallIsRefused(ObjectStorageOperationNotSupported)


@dataclass(frozen=True)
class TheSuperadminUploads(
    Scenario[
        TestSeedingSession, ARevisionAndACaller, ObjectStorageAdapter, PresignedUploadURLPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "the-superadmin-gets-an-upload-url-for-a-writable-artifact"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 쓸 수 있는 artifact 의 리비전에 객체를 올릴 URL 을 요청하면 그 객체의 "
            "저장 경로로 만든 URL 과 올릴 때 붙일 값이 반환됩니다",
            english=(
                "when the superadmin asks for a URL to upload an object to a writable artifact's "
                "revision, a URL made from the object's stored path comes back with the fields "
                "to send along"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return RESERVOIR_CONFIG

    @override
    def given(self) -> Given[TestSeedingSession, ARevisionAndACaller]:
        return ARevisionAndSomeone()

    @override
    def when(
        self,
    ) -> When[ARevisionAndACaller, ObjectStorageAdapter, PresignedUploadURLPayload]:
        return Uploading()

    @override
    def then(self) -> Then[ARevisionAndACaller, PresignedUploadURLPayload]:
        return TheUploadUrl()


@dataclass(frozen=True)
class AReadonlyArtifactRefusesUpload(
    Scenario[
        TestSeedingSession, ARevisionAndACaller, ObjectStorageAdapter, PresignedUploadURLPayload
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "uploading-to-a-readonly-artifact-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "읽기 전용 artifact 의 리비전에 객체를 올릴 URL 을 요청하면 쓸 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "when an upload URL is asked for a readonly artifact's revision, it is rejected "
                "because the artifact cannot be written"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return RESERVOIR_CONFIG

    @override
    def given(self) -> Given[TestSeedingSession, ARevisionAndACaller]:
        return ARevisionAndSomeone(readonly=True)

    @override
    def when(
        self,
    ) -> When[ARevisionAndACaller, ObjectStorageAdapter, PresignedUploadURLPayload]:
        return Uploading()

    @override
    def then(self) -> Then[ARevisionAndACaller, PresignedUploadURLPayload]:
        return TheCallIsRefused(ArtifactReadonly)


SCENARIOS: list[Scenario[Any, Any, ObjectStorageAdapter, Any]] = [
    TheSuperadminDownloads(),
    AnUnavailableRevisionIsRefused(),
    NoReservoirConfigIsRefused(),
    AVfsReservoirIsRefused(),
    TheSuperadminUploads(),
    AReadonlyArtifactRefusesUpload(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_presigned_urls(
    scenario: Scenario[Any, Any, ObjectStorageAdapter, Any],
    adapter: ObjectStorageAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
