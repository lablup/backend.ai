from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext, UploadedFilesContext
from ai.backend.test.templates.template import TestCode


class VFolderListFilesSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        upload_files_ctx = UploadedFilesContext.current()

        response = await client_session.VFolder(vfolder_meta.name).list_files("")

        assert "items" in response, "Response does not contain 'items' key."

        files_in_response = list(map(lambda x: x["name"], response["items"]))

        for file in upload_files_ctx.files:
            assert file.path in files_in_response, f"{file.path} is missing from the response"
