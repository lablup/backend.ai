from __future__ import annotations

import pytest

from ai.backend.kube.controller.volumes import (
    build_claim,
    build_volume,
    resolve_mount,
    volume_mounts,
)
from ai.backend.kube.crd.session import MountPermission, VFolderVolumeMount
from ai.backend.kube.crd.storage import (
    CSIVolumeSource,
    PersistentVolumeTemplate,
    StorageBinding,
    StorageBindingSpec,
)
from ai.backend.kube.errors import InvalidSessionWorkloadError


def _binding(name: str, base: str) -> StorageBinding:
    return StorageBinding(
        metadata={"name": name},
        spec=StorageBindingSpec(
            storage_host=f"local:{name}",
            mount_base_path=base,
            pv=PersistentVolumeTemplate(
                csi=CSIVolumeSource(
                    driver="nfs.csi.k8s.io",
                    volume_handle=name,
                    volume_attributes={"server": "10.0.0.1", "share": "/"},
                ),
                mount_options=["nfsvers=4.1"],
            ),
        ),
    )


def _mount(path: str, perm: MountPermission = MountPermission.RW) -> VFolderVolumeMount:
    return VFolderVolumeMount(
        name="data", vfid="v", host_path=path, kernel_path="/home/work/data", mount_perm=perm
    )


@pytest.fixture
def bindings() -> list[StorageBinding]:
    return [_binding("nfs", "/vfroot/nfs"), _binding("nfs-fast", "/vfroot/nfs/fast")]


class TestResolveMount:
    def test_longest_base_path_wins(self, bindings: list[StorageBinding]) -> None:
        resolved = resolve_mount(_mount("/vfroot/nfs/fast/ab/cd"), bindings)
        assert resolved.binding.metadata["name"] == "nfs-fast"
        assert resolved.subpath == "ab/cd"

    def test_prefix_must_end_at_a_path_boundary(self, bindings: list[StorageBinding]) -> None:
        resolved = resolve_mount(_mount("/vfroot/nfs/fastx/ab"), bindings)
        assert resolved.binding.metadata["name"] == "nfs"
        assert resolved.subpath == "fastx/ab"

    def test_path_outside_every_binding_is_rejected(self, bindings: list[StorageBinding]) -> None:
        with pytest.raises(InvalidSessionWorkloadError):
            resolve_mount(_mount("/vfroot/other/ab"), bindings)

    def test_dot_segments_cannot_escape(self, bindings: list[StorageBinding]) -> None:
        with pytest.raises(InvalidSessionWorkloadError):
            resolve_mount(_mount("/vfroot/nfs/../etc"), bindings)


class TestVolumeObjects:
    def test_one_volume_per_namespace_bound_to_its_claim(
        self, bindings: list[StorageBinding]
    ) -> None:
        pv = build_volume(bindings[0], "bai-p1")
        pvc = build_claim(bindings[0], "bai-p1")
        assert pv["spec"]["claimRef"] == {"namespace": "bai-p1", "name": pvc["metadata"]["name"]}
        assert pvc["spec"]["volumeName"] == pv["metadata"]["name"]
        assert pv["spec"]["csi"]["volumeHandle"] == "nfs#bai-p1"
        assert pv["spec"]["accessModes"] == ["ReadWriteMany"]

    def test_read_only_permission_mounts_read_only(self, bindings: list[StorageBinding]) -> None:
        resolved = resolve_mount(_mount("/vfroot/nfs/ab", MountPermission.RO), bindings)
        [mount] = volume_mounts([resolved])
        assert (mount["subPath"], mount["readOnly"]) == ("ab", True)
