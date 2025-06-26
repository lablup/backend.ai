from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext, VFolderContext
from ai.backend.test.data.vfolder import VFolderMeta
from ai.backend.test.templates.template import WrapperTestTemplate


class ModelVFolderTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "model_vfolder"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        client_session = ClientSessionContext.current()
        vfolder_name = f"test-{str(test_id)[:8]}"
        vfolder_cfg = VFolderContext.current()

        try:
            vfolder = await client_session.VFolder.create(
                name=vfolder_name,
                group=vfolder_cfg.group,
                unmanaged_path=vfolder_cfg.unmanaged_path,
                permission=vfolder_cfg.permission,
                usage_mode="model",
                cloneable=vfolder_cfg.cloneable,
            )

            with CreatedVFolderMetaContext.with_current(
                VFolderMeta(id=vfolder["id"], name=vfolder_name)
            ):
                yield
        finally:
            await client_session.VFolder.delete_by_id(vfolder["id"])
