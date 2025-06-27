import tempfile
from pathlib import Path

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext, UploadedFilesContext
from ai.backend.test.templates.template import TestCode


class VFolderDownloadSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        upload_files_ctx = UploadedFilesContext.current()

        with tempfile.TemporaryDirectory() as download_dir:
            download_root = Path(download_dir)

            for uploaded_file in upload_files_ctx.files:
                (download_root / uploaded_file.path).parent.mkdir(parents=True, exist_ok=True)

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
