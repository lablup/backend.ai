from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext, UploadedFilesContext
from ai.backend.test.templates.template import TestCode
from ai.backend.test.templates.vfolder.utils import retrieve_all_files


class VFolderFileRenameSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        upload_files_ctx = UploadedFilesContext.current()

        old_file_name = upload_files_ctx.files[0].path
        new_file_name = "renamed_file.txt"

        await client_session.VFolder(vfolder_meta.name).rename_file(
            old_file_name, new_name=new_file_name
        )

        files_in_response = await retrieve_all_files(client_session, vfolder_meta.name)

        assert old_file_name not in files_in_response
        assert new_file_name in files_in_response
