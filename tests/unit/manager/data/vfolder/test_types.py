from __future__ import annotations

from ai.backend.manager.data.vfolder.types import verify_vfolder_name


def test_vfolder_name_validator() -> None:
    assert not verify_vfolder_name(".bashrc")
    assert not verify_vfolder_name(".terminfo")
    assert verify_vfolder_name("bashrc")
    assert verify_vfolder_name(".config")
    assert verify_vfolder_name("bin")
    assert verify_vfolder_name("boot")
    assert verify_vfolder_name("root")
    assert not verify_vfolder_name("/bin")
    assert not verify_vfolder_name("/boot")
    assert not verify_vfolder_name("/root")
    assert verify_vfolder_name("/home/work/bin")
    assert verify_vfolder_name("/home/work/boot")
    assert verify_vfolder_name("/home/work/root")
    assert verify_vfolder_name("home/work")
    # Mounting exactly at /home/work collides with the agent's intrinsic
    # scratch mount and makes dockerd reject container creation.
    assert not verify_vfolder_name("/home/work")
