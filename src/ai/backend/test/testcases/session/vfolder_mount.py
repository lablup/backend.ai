import os
import re
import shutil
from dataclasses import dataclass
from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionMetaContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext
from ai.backend.test.templates.template import TestCode


@dataclass
class _UploadFileMeta:
    file_name: str
    full_path: str
    base_dir: str
    content: str


class FileHandlingInMountedVFolderSuccess(TestCode):
    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        session_meta = CreatedSessionMetaContext.current()
        session_name = session_meta.name

        try:
            file_upload_meta = await self._create_dummy_file()

            await client_session.VFolder(name=vfolder_meta.name).upload(
                sources=[file_upload_meta.file_name],
                basedir=file_upload_meta.base_dir,
            )
            exec_result = await client_session.ComputeSession(name=session_name).list_files(
                path=vfolder_meta.name
            )
            self._verify_file_exists(exec_result, file_upload_meta.file_name)
            await client_session.ComputeSession(name=session_name).download(
                files=[f"./{vfolder_meta.name}/{file_upload_meta.file_name}"],
                dest=f"{file_upload_meta.base_dir}/downloaded",
            )
            self._verify_downloaded_file_identical(
                original_file_path=file_upload_meta.full_path,
                downloaded_file_path=f"{file_upload_meta.base_dir}/downloaded/{file_upload_meta.file_name}",
            )
        finally:
            if file_upload_meta:
                await self._cleanup_dummy_file(file_upload_meta)

    def _verify_downloaded_file_identical(
        self, original_file_path: str, downloaded_file_path: str
    ) -> None:
        with open(original_file_path, "r", encoding="utf-8") as original_file:
            original_content = original_file.read()

        with open(downloaded_file_path, "r", encoding="utf-8") as downloaded_file:
            downloaded_content = downloaded_file.read()

        assert original_content == downloaded_content, (
            f"Downloaded file content does not match original. "
            f"Original: {original_content}, Downloaded: {downloaded_content}"
        )

    def _verify_file_exists(self, files_result: dict, original_filename: str) -> None:
        files_str = files_result.get("files", "")

        filename_pattern = r'"filename":\s*"([^"]+)"'
        matches = re.findall(filename_pattern, files_str)

        for filename in matches:
            if filename == original_filename:
                return

        raise AssertionError(f"File {original_filename} not found in the files string: {files_str}")

    async def _create_dummy_file(self) -> _UploadFileMeta:
        test_spec = TestSpecMetaContext.current()
        current_dir = os.getcwd()
        base_dir = os.path.join(current_dir, f"test_{test_spec.test_id}")

        os.makedirs(base_dir, exist_ok=True)

        file_name = f"{test_spec.test_id}.txt"
        full_path = os.path.join(base_dir, file_name)
        file_content = f"This is a dummy file for test {test_spec.test_id}."

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        return _UploadFileMeta(
            file_name=file_name, full_path=full_path, base_dir=base_dir, content=file_content
        )

    async def _cleanup_dummy_file(self, file_meta: _UploadFileMeta) -> None:
        if os.path.exists(file_meta.full_path):
            os.remove(file_meta.full_path)
        if os.path.exists(file_meta.base_dir):
            shutil.rmtree(file_meta.base_dir)
