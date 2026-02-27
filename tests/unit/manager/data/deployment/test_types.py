from pathlib import PurePosixPath
from uuid import uuid4

from ai.backend.common.types import MountPermission, VFolderID, VFolderMount, VFolderUsageMode
from ai.backend.manager.data.deployment.types import ExtraVFolderMountData, MountMetadata


def _make_vfolder_mount(
    *,
    name: str = "test",
    vfsubpath: str = ".",
    kernel_path: str = "/home/work/test",
) -> VFolderMount:
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=uuid4()),
        vfsubpath=PurePosixPath(vfsubpath),
        host_path=PurePosixPath("/data/vfolders/test"),
        kernel_path=PurePosixPath(kernel_path),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    )


class TestMountMetadataToMountSpec:
    def test_to_mount_spec_no_extra_mounts(self) -> None:
        model_id = uuid4()
        metadata = MountMetadata(model_vfolder_id=model_id)
        spec = metadata.to_mount_spec()
        assert spec.mounts == [model_id]
        assert spec.mount_map == {model_id: "/models"}
        assert spec.mount_options == {}
        assert spec.mount_subpaths == {}

    def test_to_mount_spec_extra_mount_default_subpath(self) -> None:
        model_id = uuid4()
        extra = _make_vfolder_mount(vfsubpath=".")
        metadata = MountMetadata(model_vfolder_id=model_id, extra_mounts=[extra])
        spec = metadata.to_mount_spec()
        assert extra.vfid.folder_id in spec.mounts
        assert spec.mount_subpaths == {}

    def test_to_mount_spec_extra_mount_with_subpath(self) -> None:
        model_id = uuid4()
        extra = _make_vfolder_mount(vfsubpath="subdir/data", kernel_path="/home/work/extra")
        metadata = MountMetadata(model_vfolder_id=model_id, extra_mounts=[extra])
        spec = metadata.to_mount_spec()
        assert spec.mount_subpaths == {extra.vfid.folder_id: "subdir/data"}

    def test_to_mount_spec_mixed_subpaths(self) -> None:
        model_id = uuid4()
        default_mount = _make_vfolder_mount(
            name="default", vfsubpath=".", kernel_path="/home/work/default"
        )
        sub_mount = _make_vfolder_mount(
            name="custom", vfsubpath="nested/dir", kernel_path="/home/work/custom"
        )
        metadata = MountMetadata(
            model_vfolder_id=model_id,
            extra_mounts=[default_mount, sub_mount],
        )
        spec = metadata.to_mount_spec()
        assert default_mount.vfid.folder_id not in spec.mount_subpaths
        assert spec.mount_subpaths == {sub_mount.vfid.folder_id: "nested/dir"}


class TestExtraVFolderMountData:
    def test_default_subpath(self) -> None:
        data = ExtraVFolderMountData(
            vfolder_id=uuid4(),
            mount_destination="/home/work/data",
        )
        assert data.subpath == "."

    def test_custom_subpath(self) -> None:
        data = ExtraVFolderMountData(
            vfolder_id=uuid4(),
            mount_destination="/home/work/data",
            subpath="custom/path",
        )
        assert data.subpath == "custom/path"
