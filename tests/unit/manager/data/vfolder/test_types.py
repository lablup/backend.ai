from __future__ import annotations

from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, verify_vfolder_name


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


class TestVFolderOperationStatusSets:
    def test_hard_deleted_holds_the_statuses_whose_storage_is_gone_or_failed(self) -> None:
        assert VFolderOperationStatus.hard_deleted() == frozenset({
            VFolderOperationStatus.DELETE_COMPLETE,
            VFolderOperationStatus.DELETE_ERROR,
        })

    def test_dead_holds_the_trashed_and_the_hard_deleted_statuses(self) -> None:
        assert VFolderOperationStatus.dead() == (
            frozenset({
                VFolderOperationStatus.DELETE_PENDING,
                VFolderOperationStatus.DELETE_ONGOING,
            })
            | VFolderOperationStatus.hard_deleted()
        )

    def test_dead_leaves_out_every_status_a_session_may_mount(self) -> None:
        mountable = {
            VFolderOperationStatus.READY,
            VFolderOperationStatus.CREATING,
            VFolderOperationStatus.PERFORMING,
            VFolderOperationStatus.CLONING,
            VFolderOperationStatus.MOUNTED,
            VFolderOperationStatus.ERROR,
        }
        assert mountable.isdisjoint(VFolderOperationStatus.dead())
