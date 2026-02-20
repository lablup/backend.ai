from typing import Any
from uuid import UUID, uuid4

from ai.backend.manager.data.deployment.types import MountSpec
from ai.backend.manager.models.vfolder.utils import merge_mount_options_with_subpaths


class TestMergeMountOptionsWithSubpaths:
    def test_empty_mount_spec(self) -> None:
        spec = MountSpec(mounts=[], mount_map={}, mount_options={}, mount_subpaths={})
        result = merge_mount_options_with_subpaths(spec)
        assert result == {}

    def test_options_only_no_subpaths(self) -> None:
        vf_id = uuid4()
        opts: dict[UUID, dict[str, Any]] = {vf_id: {"permission": "rw"}}
        spec = MountSpec(mounts=[vf_id], mount_map={}, mount_options=opts, mount_subpaths={})
        result = merge_mount_options_with_subpaths(spec)
        assert result == {vf_id: {"permission": "rw"}}

    def test_subpaths_only_no_options(self) -> None:
        vf_id = uuid4()
        spec = MountSpec(
            mounts=[vf_id], mount_map={}, mount_options={}, mount_subpaths={vf_id: "data/sub"}
        )
        result = merge_mount_options_with_subpaths(spec)
        assert result == {vf_id: {"subpath": "data/sub"}}

    def test_merge_subpath_into_existing_options(self) -> None:
        vf_id = uuid4()
        opts: dict[UUID, dict[str, Any]] = {vf_id: {"permission": "ro"}}
        spec = MountSpec(
            mounts=[vf_id],
            mount_map={},
            mount_options=opts,
            mount_subpaths={vf_id: "models/v2"},
        )
        result = merge_mount_options_with_subpaths(spec)
        assert result == {vf_id: {"permission": "ro", "subpath": "models/v2"}}

    def test_subpath_for_new_vfolder_id(self) -> None:
        vf_id_a = uuid4()
        vf_id_b = uuid4()
        opts: dict[UUID, dict[str, Any]] = {vf_id_a: {"permission": "rw"}}
        spec = MountSpec(
            mounts=[vf_id_a, vf_id_b],
            mount_map={},
            mount_options=opts,
            mount_subpaths={vf_id_b: "extra/path"},
        )
        result = merge_mount_options_with_subpaths(spec)
        assert result == {
            vf_id_a: {"permission": "rw"},
            vf_id_b: {"subpath": "extra/path"},
        }

    def test_does_not_mutate_original(self) -> None:
        vf_id = uuid4()
        original_opts: dict[str, Any] = {"permission": "rw"}
        opts: dict[UUID, dict[str, Any]] = {vf_id: original_opts}
        spec = MountSpec(
            mounts=[vf_id],
            mount_map={},
            mount_options=opts,
            mount_subpaths={vf_id: "sub"},
        )
        merge_mount_options_with_subpaths(spec)
        assert "subpath" not in original_opts
