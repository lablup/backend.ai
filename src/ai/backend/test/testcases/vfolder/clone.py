from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext
from ai.backend.test.templates.template import TestCode
from ai.backend.test.templates.vfolder.utils import retrieve_all_files


class VFolderCloneSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()

        new_folder_name = vfolder_meta.name + "_cloned"
        await client_session.VFolder(vfolder_meta.name).clone(target_name=new_folder_name)

        old_vfolder_files = await retrieve_all_files(client_session, vfolder_meta.name)
        new_vfolder_files = await retrieve_all_files(client_session, new_folder_name)

        assert old_vfolder_files == new_vfolder_files, (
            "Files in the cloned VFolder do not match the original VFolder."
        )
