"""폴더 안의 파일과 디렉터리 다루기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.request import (
    CreateDownloadSessionInput,
    CreateUploadSessionInput,
    DeleteFilesInput,
    ListFilesInput,
    MkdirInput,
    MoveFileInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    CreateDownloadSessionPayload,
    CreateUploadSessionPayload,
    DeleteFilesPayload,
    ListFilesPayload,
    MkdirPayload,
    MoveFilePayload,
)
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.vfolder import AFolderAndPeople, SomeoneWithAFolder
from bai_scenario.fakes.storage_proxy import (
    CLIENT_API_BASE_URL,
    DELETE_TASK_ID,
    DOWNLOAD_TOKEN,
    UPLOAD_TOKEN,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type FileStep = Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, Any]


@dataclass(frozen=True)
class ListingTheFiles(When[AFolderAndPeople, VFolderAdapter, ListFilesPayload]):
    @override
    def operation(self) -> str:
        return "list_files"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 의 파일 목록을 조회합니다",
            english=f"{laid.caller.username} lists the files of the {laid.folder.name} vfolder",
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> ListFilesPayload:
        with ActingAs(laid.caller):
            return await adapter.list_files(laid.folder.id, ListFilesInput(path="."))


@dataclass(frozen=True)
class MakingDirectories(When[AFolderAndPeople, VFolderAdapter, MkdirPayload]):
    @override
    def operation(self) -> str:
        return "mkdir"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 안에 디렉터리 둘을 만듭니다",
            english=(
                f"{laid.caller.username} makes two directories inside the {laid.folder.name} "
                "vfolder"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> MkdirPayload:
        with ActingAs(laid.caller):
            return await adapter.mkdir(laid.folder.id, MkdirInput(path=["new", "other"]))


@dataclass(frozen=True)
class MovingAFile(When[AFolderAndPeople, VFolderAdapter, MoveFilePayload]):
    @override
    def operation(self) -> str:
        return "move_file"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 안에서 파일 하나를 옮깁니다",
            english=(
                f"{laid.caller.username} moves one file inside the {laid.folder.name} vfolder"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> MoveFilePayload:
        with ActingAs(laid.caller):
            return await adapter.move_file(
                laid.folder.id, MoveFileInput(src="hello.txt", dst="data/hello.txt")
            )


@dataclass(frozen=True)
class DeletingFiles(When[AFolderAndPeople, VFolderAdapter, DeleteFilesPayload]):
    @override
    def operation(self) -> str:
        return "delete_files"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 안의 파일 하나를 지웁니다",
            english=(
                f"{laid.caller.username} deletes one file inside the {laid.folder.name} vfolder"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> DeleteFilesPayload:
        with ActingAs(laid.caller):
            return await adapter.delete_files(laid.folder.id, DeleteFilesInput(files=["hello.txt"]))


@dataclass(frozen=True)
class OpeningAnUploadSession(When[AFolderAndPeople, VFolderAdapter, CreateUploadSessionPayload]):
    @override
    def operation(self) -> str:
        return "create_upload_session"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 에 올릴 세션을 엽니다",
            english=(
                f"{laid.caller.username} opens an upload session for the {laid.folder.name} vfolder"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndPeople
    ) -> CreateUploadSessionPayload:
        with ActingAs(laid.caller):
            return await adapter.create_upload_session(
                laid.folder.id, CreateUploadSessionInput(path="upload.txt", size=5)
            )


@dataclass(frozen=True)
class OpeningADownloadSession(When[AFolderAndPeople, VFolderAdapter, CreateDownloadSessionPayload]):
    @override
    def operation(self) -> str:
        return "create_download_session"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 에서 내려받을 세션을 엽니다",
            english=(
                f"{laid.caller.username} opens a download session for the {laid.folder.name} "
                "vfolder"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndPeople
    ) -> CreateDownloadSessionPayload:
        with ActingAs(laid.caller):
            return await adapter.create_download_session(
                laid.folder.id, CreateDownloadSessionInput(path="hello.txt")
            )


@dataclass(frozen=True)
class TheFiles(Then[AFolderAndPeople, ListFilesPayload]):
    @override
    def says(self) -> str:
        return Says(
            "저장소가 답한 파일 목록 전체가 응답으로 옵니다",
            english="the whole file list the storage answered comes back",
        )

    @override
    def look(self, laid: AFolderAndPeople, answered: Answered[ListFilesPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("items.length", len(payload.items), 2)]
        if len(payload.items) != 2:
            return verdicts
        first, second = payload.items
        verdicts.extend([
            Same("items[0].name", first.name, "hello.txt"),
            Same("items[0].type", first.type, "FILE"),
            Same("items[0].size", first.size, 5),
            Same("items[0].mode", first.mode, 33188),
            Same("items[0].created_at", first.created_at, "2026-01-01 00:00:00"),
            Same("items[0].updated_at", first.updated_at, "2026-01-02 00:00:00"),
            Same("items[1].name", second.name, "data"),
            Same("items[1].type", second.type, "DIRECTORY"),
            Same("items[1].size", second.size, 0),
            Same("items[1].mode", second.mode, 16877),
            Same("items[1].created_at", second.created_at, "2026-01-01 00:00:00"),
            Same("items[1].updated_at", second.updated_at, "2026-01-01 00:00:00"),
        ])
        return verdicts


@dataclass(frozen=True)
class TheDirectories(Then[AFolderAndPeople, MkdirPayload]):
    @override
    def says(self) -> str:
        return Says(
            "만든 디렉터리 경로가 응답으로 옵니다",
            english="the paths of the directories made come back",
        )

    @override
    def look(self, laid: AFolderAndPeople, answered: Answered[MkdirPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("results", payload.results, ["new", "other"])]


@dataclass(frozen=True)
class TheMovedFile(Then[AFolderAndPeople, MoveFilePayload]):
    @override
    def says(self) -> str:
        return Says(
            "옮긴 파일의 출발지와 도착지가 응답으로 옵니다",
            english="where the file was moved from and to comes back",
        )

    @override
    def look(self, laid: AFolderAndPeople, answered: Answered[MoveFilePayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("src", payload.src, "hello.txt"),
            Same("dst", payload.dst, "data/hello.txt"),
        ]


@dataclass(frozen=True)
class TheDeletionTask(Then[AFolderAndPeople, DeleteFilesPayload]):
    @override
    def says(self) -> str:
        return Says(
            "삭제를 맡은 background task 의 id 가 응답으로 옵니다",
            english="the id of the background task doing the deletion comes back",
        )

    @override
    def look(self, laid: AFolderAndPeople, answered: Answered[DeleteFilesPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("bgtask_id", payload.bgtask_id, str(DELETE_TASK_ID))]


@dataclass(frozen=True)
class TheUploadSession(Then[AFolderAndPeople, CreateUploadSessionPayload]):
    @override
    def says(self) -> str:
        return Says(
            "올리기에 쓸 token 과 주소가 응답으로 옵니다",
            english="the token and address to upload to come back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[CreateUploadSessionPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("token", payload.token, UPLOAD_TOKEN),
            Same("url", payload.url, str(CLIENT_API_BASE_URL / "upload")),
        ]


@dataclass(frozen=True)
class TheDownloadSession(Then[AFolderAndPeople, CreateDownloadSessionPayload]):
    @override
    def says(self) -> str:
        return Says(
            "내려받기에 쓸 token 과 주소가 응답으로 옵니다",
            english="the token and address to download from come back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[CreateDownloadSessionPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("token", payload.token, DOWNLOAD_TOKEN),
            Same("url", payload.url, str(CLIENT_API_BASE_URL / "download")),
        ]


@dataclass(frozen=True)
class AGrantedReaderListsTheFiles(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, ListFilesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-lists-the-files"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 읽기 권한을 받은 사용자가 폴더의 파일 목록을 조회하면, 저장소가 답한 목록이 "
            "응답으로 옵니다",
            english=(
                "when a user granted vfolder read lists the files of the folder, the list the "
                "storage answered comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.READ,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, ListFilesPayload]:
        return ListingTheFiles()

    @override
    def then(self) -> Then[AFolderAndPeople, ListFilesPayload]:
        return TheFiles()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotListTheFiles(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, ListFilesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-list-the-files"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 폴더의 파일 목록을 조회하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to list the files of a folder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, ListFilesPayload]:
        return ListingTheFiles()

    @override
    def then(self) -> Then[AFolderAndPeople, ListFilesPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedWriterMakesDirectories(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, MkdirPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-update-makes-directories"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 수정 권한을 받은 사용자가 폴더 안에 디렉터리를 만들면, 만든 경로가 "
            "응답으로 옵니다",
            english=(
                "when a user granted vfolder update makes directories inside the folder, the "
                "paths made come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, MkdirPayload]:
        return MakingDirectories()

    @override
    def then(self) -> Then[AFolderAndPeople, MkdirPayload]:
        return TheDirectories()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMakeDirectories(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, MkdirPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-make-directories"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 폴더 안에 디렉터리를 만들려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to make directories inside a folder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, MkdirPayload]:
        return MakingDirectories()

    @override
    def then(self) -> Then[AFolderAndPeople, MkdirPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedWriterMovesAFile(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, MoveFilePayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-update-moves-a-file"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 수정 권한을 받은 사용자가 폴더 안에서 파일을 옮기면, 출발지와 도착지가 "
            "응답으로 옵니다",
            english=(
                "when a user granted vfolder update moves a file inside the folder, where it "
                "came from and went to comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, MoveFilePayload]:
        return MovingAFile()

    @override
    def then(self) -> Then[AFolderAndPeople, MoveFilePayload]:
        return TheMovedFile()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMoveAFile(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, MoveFilePayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-move-a-file"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 폴더 안에서 파일을 옮기려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to move a file inside a folder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, MoveFilePayload]:
        return MovingAFile()

    @override
    def then(self) -> Then[AFolderAndPeople, MoveFilePayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedWriterDeletesFiles(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, DeleteFilesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-update-deletes-files"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 수정 권한을 받은 사용자가 폴더 안의 파일을 지우면, 삭제를 맡은 "
            "background task 의 id 가 응답으로 옵니다",
            english=(
                "when a user granted vfolder update deletes files inside the folder, the id of "
                "the background task doing it comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, DeleteFilesPayload]:
        return DeletingFiles()

    @override
    def then(self) -> Then[AFolderAndPeople, DeleteFilesPayload]:
        return TheDeletionTask()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDeleteFiles(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, DeleteFilesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-files"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 폴더 안의 파일을 지우려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to delete files inside a folder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, DeleteFilesPayload]:
        return DeletingFiles()

    @override
    def then(self) -> Then[AFolderAndPeople, DeleteFilesPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedWriterOpensAnUploadSession(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, CreateUploadSessionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-create-opens-an-upload-session"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 생성 권한을 받은 사용자가 폴더에 올릴 세션을 열면, 올리기에 쓸 token 과 "
            "주소가 응답으로 옵니다",
            english=(
                "when a user granted vfolder create opens an upload session for the folder, the "
                "token and address to upload to come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.CREATE,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, CreateUploadSessionPayload]:
        return OpeningAnUploadSession()

    @override
    def then(self) -> Then[AFolderAndPeople, CreateUploadSessionPayload]:
        return TheUploadSession()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotOpenAnUploadSession(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, CreateUploadSessionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-open-an-upload-session"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 폴더에 올릴 세션을 열려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to open an upload session for a folder, it "
                "is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, CreateUploadSessionPayload]:
        return OpeningAnUploadSession()

    @override
    def then(self) -> Then[AFolderAndPeople, CreateUploadSessionPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedReaderOpensADownloadSession(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, CreateDownloadSessionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-opens-a-download-session"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 읽기 권한을 받은 사용자가 폴더에서 내려받을 세션을 열면, 내려받기에 쓸 "
            "token 과 주소가 응답으로 옵니다",
            english=(
                "when a user granted vfolder read opens a download session for the folder, the "
                "token and address to download from come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.READ,))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, CreateDownloadSessionPayload]:
        return OpeningADownloadSession()

    @override
    def then(self) -> Then[AFolderAndPeople, CreateDownloadSessionPayload]:
        return TheDownloadSession()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotOpenADownloadSession(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, CreateDownloadSessionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-open-a-download-session"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 폴더에서 내려받을 세션을 열려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted nothing tries to open a download session for a folder, it "
                "is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder()

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, CreateDownloadSessionPayload]:
        return OpeningADownloadSession()

    @override
    def then(self) -> Then[AFolderAndPeople, CreateDownloadSessionPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[FileStep] = [
    AGrantedReaderListsTheFiles(),
    AUserGrantedNothingMayNotListTheFiles(),
    AGrantedWriterMakesDirectories(),
    AUserGrantedNothingMayNotMakeDirectories(),
    AGrantedWriterMovesAFile(),
    AUserGrantedNothingMayNotMoveAFile(),
    AGrantedWriterDeletesFiles(),
    AUserGrantedNothingMayNotDeleteFiles(),
    AGrantedWriterOpensAnUploadSession(),
    AUserGrantedNothingMayNotOpenAnUploadSession(),
    AGrantedReaderOpensADownloadSession(),
    AUserGrantedNothingMayNotOpenADownloadSession(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_files(
    scenario: FileStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
