import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from pathlib import Path
from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.contexts.vfolder import (
    CreatedVFolderMetaContext,
    UploadedFilesContext,
    UploadFilesContext,
)
from ai.backend.test.data.vfolder import UploadedFile, UploadedFilesMeta
from ai.backend.test.templates.template import WrapperTestTemplate


class PlainTextFilesUploader(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "upload_plain_text_files"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        test_dirname = f"test-{str(test_id)[:8]}"

        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        upload_deps = UploadFilesContext.current()

        uploaded_files: list[UploadedFile] = []

        with tempfile.TemporaryDirectory() as upload_dir:
            upload_root = Path(upload_dir)

            for dep in upload_deps:
                local_path = upload_root / dep.path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_text(dep.content)

                uploaded_files.append(
                    UploadedFile(
                        path=f"{test_dirname}/{dep.path}",
                        content=dep.content,
                    )
                )

            upload_files = []
            for dep in upload_deps:
                upload_files.append(upload_root / dep.path)

            await client_session.VFolder(vfolder_meta.name).upload(
                upload_files,
                basedir=upload_root,
                dst_dir=test_dirname,
                recursive=True,
            )

            with UploadedFilesContext.with_current(
                UploadedFilesMeta(
                    files=uploaded_files,
                    uploaded_path=upload_root,
                )
            ):
                yield
