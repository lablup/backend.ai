import tempfile
from pathlib import Path

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext, UploadedFilesContext
from ai.backend.test.templates.template import TestCode


class VFolderDownloadSuccess(TestCode):
    async def test(self) -> None:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        test_dirname = f"test-{str(test_id)[:8]}"

        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()

        upload_files_ctx = UploadedFilesContext.current()

        with tempfile.TemporaryDirectory() as download_dir:
            download_root = Path(download_dir)
            (download_root / test_dirname / "nested").mkdir(parents=True, exist_ok=True)

            for uploaded_file in upload_files_ctx.files:
                await client_session.VFolder(vfolder_meta.name).download(
                    [uploaded_file.path],
                    basedir=download_root,
                    max_retries=3,
                )

                local_path = download_root / uploaded_file.path
                assert local_path.exists(), f"{local_path} is missing"
                assert local_path.read_text() == uploaded_file.content, (
                    f"{local_path} file content mismatch"
                )
