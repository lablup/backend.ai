from typing import override
from uuid import UUID

from ai.backend.client.output.fields import session_node_fields
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.contexts.vfolder import CreatedVFolderMetaContext
from ai.backend.test.templates.template import TestCode


class VFolderMountByUUIDTest(TestCode):
    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        image_ctx = ImageContext.current()
        test_id = TestSpecMetaContext.current().test_id

        vfolder_info = await client_session.VFolder(name=vfolder_meta.name).info()
        vfolder_uuid = vfolder_info["id"]

        session_name = f"uuid-mounts-{test_id}"

        session = await client_session.ComputeSession.get_or_create(
            image_ctx.name,
            architecture=image_ctx.architecture,
            name=session_name,
            mount_ids=[vfolder_uuid],
            mount_id_map={vfolder_uuid: "/home/work/some/path"},
        )

        try:
            assert session.id is not None
            result = await client_session.ComputeSession.from_session_id(session.id).detail([
                session_node_fields["vfolder_mounts"]
            ])
            assert UUID(vfolder_info["id"]) == UUID(result["vfolder_mounts"][0])

            result = await client_session.ComputeSession(name=session_name).list_files(
                path="/home/work/some/path"
            )
            assert isinstance(result, dict) and "files" in result
        finally:
            await client_session.ComputeSession(name=session_name).destroy()


class VFolderMountByNameTest(TestCode):
    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        vfolder_meta = CreatedVFolderMetaContext.current()
        image_ctx = ImageContext.current()
        test_id = TestSpecMetaContext.current().test_id

        vfolder_info = await client_session.VFolder(name=vfolder_meta.name).info()
        vfolder_name = vfolder_info["name"]

        session_name = f"uuid-mounts-{test_id}"

        session = await client_session.ComputeSession.get_or_create(
            image_ctx.name,
            architecture=image_ctx.architecture,
            name=session_name,
            mounts=[vfolder_name],
            mount_map={vfolder_name: "/home/work/some/path"},
        )

        try:
            assert session.id is not None
            result = await client_session.ComputeSession.from_session_id(session.id).detail([
                session_node_fields["vfolder_mounts"]
            ])
            assert UUID(vfolder_info["id"]) == UUID(result["vfolder_mounts"][0])

            result = await client_session.ComputeSession(name=session_name).list_files(
                path="/home/work/some/path"
            )
            assert isinstance(result, dict) and "files" in result
        finally:
            await client_session.ComputeSession(name=session_name).destroy()
