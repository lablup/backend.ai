from pathlib import Path

from ai.backend.common.json import load_json
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionMetaContext
from ai.backend.test.templates.template import TestCode


class FileExistenceCheck(TestCode):
    _path: Path
    _checklist: list[str]

    def __init__(self, path: Path, checklist: list[str]) -> None:
        super().__init__()
        self._path = path
        self._checklist = checklist

    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()

        response = await client_session.ComputeSession(str(session_meta.id)).list_files(self._path)
        files = load_json(response["files"])

        actual_files = [file["filename"] for file in files if file["filename"] in self._checklist]
        assert actual_files == self._checklist, (
            f"Expected files: {self._checklist}, but got following files: {files}"
        )
