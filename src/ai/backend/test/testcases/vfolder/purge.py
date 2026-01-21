from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.contexts.vfolder import VFolderContext
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import UnexpectedSuccess


class VFolderPurgeSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id

        vfolder_name = f"test-{str(test_id)[:8]}"
        vfolder_cfg = VFolderContext.current()

        await client_session.VFolder.create(
            name=vfolder_name,
            group=vfolder_cfg.group,
            unmanaged_path=vfolder_cfg.unmanaged_path,
            permission=vfolder_cfg.permission,
            usage_mode="general",
            cloneable=vfolder_cfg.cloneable,
        )

        try:
            await client_session.VFolder(str(vfolder_name)).purge()
            raise UnexpectedSuccess("VFolder purge should be not allowed before deletion")
        except Exception:
            pass

        await client_session.VFolder(str(vfolder_name)).delete()

        vfolder_info = await client_session.VFolder(str(vfolder_name)).info()
        assert vfolder_info["status"] == "delete-pending", (
            "VFolder is not soft-deleted successfully"
        )

        await client_session.VFolder(str(vfolder_name)).purge()

        try:
            vfolder_info = await client_session.VFolder(str(vfolder_name)).info()
            raise UnexpectedSuccess("VFolder info should not be retrievable after purge")
        except Exception:
            pass
