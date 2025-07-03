import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import (
    CreatedVFolderMetaContext,
    UploadedFilesContext,
    UploadFilesContext,
)
from ai.backend.test.data.vfolder import UploadedFile, UploadedFilesMeta
from ai.backend.test.templates.template import WrapperTestTemplate
from ai.backend.test.templates.vfolder.utils import retrieve_all_files


class PlainTextFilesUploader(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "upload_plain_text_files"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        upload_deps = UploadFilesContext.current()

        uploaded_files: list[UploadedFile] = []

        with tempfile.TemporaryDirectory() as upload_dir:
            upload_root = Path(upload_dir).resolve()
            upload_paths = []

            for upload_dep in upload_deps:
                upload_path = upload_root / upload_dep.path
                upload_path.parent.mkdir(parents=True, exist_ok=True)
                upload_path.write_text(upload_dep.content)
                upload_paths.append(upload_path)

                uploaded_files.append(
                    UploadedFile(
                        path=upload_dep.path,
                        content=upload_dep.content,
                    )
                )

            await client_session.VFolder(vfolder_meta.name).upload(
                upload_paths,
                basedir=upload_root,
                recursive=True,
            )

            response = await client_session.VFolder(vfolder_meta.name).list_files()

            assert "items" in response, "Response does not contain 'items' key."
            assert len(response["items"]) > 0, "Response items list is empty."

            upload_requested_files = {uploaded_file.path for uploaded_file in uploaded_files}
            files_in_response = await retrieve_all_files(client_session, vfolder_meta.name)

            for upload_requested_file in upload_requested_files:
                assert upload_requested_file in files_in_response, (
                    f"Uploaded file '{upload_requested_file}' not found in response. Available files: {files_in_response}"
                )

            with UploadedFilesContext.with_current(
                UploadedFilesMeta(
                    files=uploaded_files,
                    uploaded_path=upload_root,
                )
            ):
                yield
