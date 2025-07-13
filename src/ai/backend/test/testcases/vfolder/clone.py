from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext
from ai.backend.test.templates.session.utils import verify_bgtask_events
from ai.backend.test.templates.template import TestCode
from ai.backend.test.templates.vfolder.utils import retrieve_all_files


class VFolderCloneSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()

        new_vfolder_name = vfolder_meta.name + "_cloned"
        response = await client_session.VFolder(vfolder_meta.name).clone(
            target_name=new_vfolder_name
        )

        await verify_bgtask_events(
            client_session,
            response["bgtask_id"],
            BgtaskStatus.DONE,
            {BgtaskStatus.FAILED, BgtaskStatus.CANCELLED, BgtaskStatus.PARTIAL_SUCCESS},
        )

        old_vfolder_files = await retrieve_all_files(client_session, vfolder_meta.name)
        new_vfolder_files = await retrieve_all_files(client_session, new_vfolder_name)

        assert old_vfolder_files == new_vfolder_files, (
            "Files in the cloned VFolder do not match the original VFolder."
        )

        await client_session.VFolder.delete_by_id(response["id"])
        await client_session.VFolder(response["name"]).purge()
