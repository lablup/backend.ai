from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext
from ai.backend.test.templates.template import TestCode


class VFolderDeleteAndRestoreSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()

        try:
            await client_session.VFolder(str(vfolder_meta.name)).delete()
        except Exception as e:
            raise AssertionError(f"Failed to delete vfolder: {e}")

        vfolder_info = await client_session.VFolder(str(vfolder_meta.name)).info()
        assert vfolder_info["status"] == "delete-pending", (
            "VFolder is not soft-deleted successfully"
        )

        try:
            await client_session.VFolder(str(vfolder_meta.name)).restore()
        except Exception as e:
            raise AssertionError(f"Failed to restore vfolder: {e}")

        vfolder_info = await client_session.VFolder(str(vfolder_meta.name)).info()
        assert vfolder_info["status"] == "ready", "VFolder is not restored successfully"
