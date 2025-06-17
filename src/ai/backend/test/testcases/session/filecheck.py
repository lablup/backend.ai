from pathlib import Path

from ai.backend.common.json import load_json
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionIDContext
from ai.backend.test.templates.template import TestCode


class FileCheckTest(TestCode):
    _path: Path
    _expected_filenames: list[str]

    def __init__(self, path: Path, expected_filenames: list[str]) -> None:
        super().__init__()
        self._path = path
        self._expected_filenames = expected_filenames

    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_id = CreatedSessionIDContext.current()

        response = await client_session.ComputeSession(str(session_id)).list_files(self._path)
        files = load_json(response["files"])

        actual_files = [
            file["filename"] for file in files if file["filename"] in self._expected_filenames
        ]
        assert actual_files == self._expected_filenames, (
            f"Expected files: {self._expected_filenames}, but got: {actual_files}"
        )
