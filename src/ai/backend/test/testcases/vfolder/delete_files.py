from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext, UploadedFilesContext
from ai.backend.test.templates.template import TestCode
from ai.backend.test.templates.vfolder.utils import retrieve_all_files


class VFolderFilesDeletionSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        upload_files_ctx = UploadedFilesContext.current()

        old_file0_name = upload_files_ctx.files[0].path
        old_file1_name = upload_files_ctx.files[1].path

        await client_session.VFolder(vfolder_meta.name).delete_files(
            [old_file0_name, old_file1_name], recursive=False
        )

        files_in_response = await retrieve_all_files(client_session, vfolder_meta.name)

        assert old_file0_name not in files_in_response
        assert old_file1_name not in files_in_response


class VFolderFilesRecursiveDeletionSuccess(TestCode):
    _dirname_to_delete: str

    def __init__(self, dirname_to_delete: str) -> None:
        self._dirname_to_delete = dirname_to_delete

    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()

        await client_session.VFolder(vfolder_meta.name).delete_files(
            [self._dirname_to_delete], recursive=True
        )

        files_in_response = await retrieve_all_files(client_session, vfolder_meta.name)

        assert self._dirname_to_delete not in files_in_response, (
            f"Directory {self._dirname_to_delete} was not deleted"
        )
