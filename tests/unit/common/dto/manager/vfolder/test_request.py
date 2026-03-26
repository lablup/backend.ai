"""Tests for VFolder request DTOs."""

import uuid

import pytest

from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.dto.manager.vfolder.request import (
    AcceptInvitationReq,
    ChangeVFolderOwnershipReq,
    CloneVFolderReq,
    CreateDownloadSessionReq,
    CreateUploadSessionReq,
    DeleteFilesAsyncBodyParam,
    DeleteFilesAsyncPathParam,
    DeleteFilesReq,
    DeleteInvitationReq,
    DeleteVFolderByIDReq,
    DeleteVFolderFromTrashReq,
    GetFstabContentsQuery,
    GetQuotaQuery,
    GetUsageQuery,
    GetUsedBytesQuery,
    GetVFolderIDReq,
    GetVolumePerfMetricQuery,
    InviteVFolderReq,
    LeaveVFolderReq,
    ListFilesQuery,
    ListHostsQuery,
    ListSharedVFoldersQuery,
    ListVFoldersQuery,
    MkdirReq,
    MountHostReq,
    MoveFileReq,
    PurgeVFolderReq,
    RenameFileReq,
    RenameVFolderReq,
    RestoreVFolderReq,
    ShareVFolderReq,
    UmountHostReq,
    UnshareVFolderReq,
    UpdateInvitationReq,
    UpdateQuotaReq,
    UpdateSharedVFolderReq,
    UpdateVFolderOptionsReq,
    UpdateVFolderSharingStatusReq,
    UserPermMapping,
    VFolderCreateReq,
)
from ai.backend.common.types import VFolderUsageMode


class TestVFolderCreateReq:
    def test_minimal_creation(self) -> None:
        req = VFolderCreateReq(name="test-folder")
        assert req.name == "test-folder"
        assert req.folder_host is None
        assert req.usage_mode == VFolderUsageMode.GENERAL
        assert req.permission == VFolderPermissionField.READ_WRITE
        assert req.cloneable is False

    def test_full_creation(self) -> None:
        gid = uuid.uuid4()
        req = VFolderCreateReq(
            name="my-folder",
            folder_host="storage-host",
            usage_mode=VFolderUsageMode.MODEL,
            permission=VFolderPermissionField.READ_ONLY,
            cloneable=True,
            group_id=gid,
        )
        assert req.name == "my-folder"
        assert req.folder_host == "storage-host"
        assert req.usage_mode == VFolderUsageMode.MODEL
        assert req.permission == VFolderPermissionField.READ_ONLY
        assert req.cloneable is True
        assert req.group_id == gid

    def test_group_id_alias_groupId(self) -> None:
        gid = uuid.uuid4()
        req = VFolderCreateReq.model_validate({"name": "test", "groupId": str(gid)})
        assert req.group_id == gid

    def test_group_id_alias_group(self) -> None:
        gid = uuid.uuid4()
        req = VFolderCreateReq.model_validate({"name": "test", "group": str(gid)})
        assert req.group_id == gid

    def test_host_alias(self) -> None:
        req = VFolderCreateReq.model_validate({"name": "test", "host": "my-host"})
        assert req.folder_host == "my-host"

    def test_unmanaged_path_alias(self) -> None:
        req = VFolderCreateReq.model_validate({"name": "test", "unmanagedPath": "/mnt/data"})
        assert req.unmanaged_path == "/mnt/data"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(Exception):
            VFolderCreateReq.model_validate({})


class TestRenameVFolderReq:
    def test_valid(self) -> None:
        req = RenameVFolderReq(new_name="new-folder")
        assert req.new_name == "new-folder"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(Exception):
            RenameVFolderReq.model_validate({})


class TestDeleteVFolderByIDReq:
    def test_alias_vfolderId(self) -> None:
        vid = uuid.uuid4()
        req = DeleteVFolderByIDReq.model_validate({"vfolderId": str(vid)})
        assert req.vfolder_id == vid

    def test_alias_id(self) -> None:
        vid = uuid.uuid4()
        req = DeleteVFolderByIDReq.model_validate({"id": str(vid)})
        assert req.vfolder_id == vid


class TestDeleteVFolderFromTrashReq:
    def test_alias_id(self) -> None:
        vid = uuid.uuid4()
        req = DeleteVFolderFromTrashReq.model_validate({"id": str(vid)})
        assert req.vfolder_id == vid

    def test_alias_vfolderId(self) -> None:
        vid = uuid.uuid4()
        req = DeleteVFolderFromTrashReq.model_validate({"vfolderId": str(vid)})
        assert req.vfolder_id == vid


class TestPurgeVFolderReq:
    def test_alias(self) -> None:
        vid = uuid.uuid4()
        req = PurgeVFolderReq.model_validate({"id": str(vid)})
        assert req.vfolder_id == vid


class TestRestoreVFolderReq:
    def test_alias(self) -> None:
        vid = uuid.uuid4()
        req = RestoreVFolderReq.model_validate({"vfolderId": str(vid)})
        assert req.vfolder_id == vid


class TestCloneVFolderReq:
    def test_defaults(self) -> None:
        req = CloneVFolderReq(target_name="clone-folder")
        assert req.target_name == "clone-folder"
        assert req.target_host is None
        assert req.cloneable is False
        assert req.usage_mode == VFolderUsageMode.GENERAL
        assert req.permission == VFolderPermissionField.READ_WRITE

    def test_target_host_alias(self) -> None:
        req = CloneVFolderReq.model_validate({"target_name": "clone", "folder_host": "storage-1"})
        assert req.target_host == "storage-1"


class TestGetVFolderIDReq:
    def test_alias_vfolderName(self) -> None:
        req = GetVFolderIDReq.model_validate({"vfolderName": "my-folder"})
        assert req.name == "my-folder"

    def test_alias_vfolder_name(self) -> None:
        req = GetVFolderIDReq.model_validate({"vfolder_name": "my-folder"})
        assert req.name == "my-folder"


class TestUpdateVFolderOptionsReq:
    def test_all_none_defaults(self) -> None:
        req = UpdateVFolderOptionsReq.model_validate({})
        assert req.cloneable is None
        assert req.permission is None

    def test_set_values(self) -> None:
        req = UpdateVFolderOptionsReq(cloneable=True, permission=VFolderPermissionField.READ_ONLY)
        assert req.cloneable is True
        assert req.permission == VFolderPermissionField.READ_ONLY


class TestListVFoldersQuery:
    def test_defaults(self) -> None:
        query = ListVFoldersQuery.model_validate({})
        assert query.all is False
        assert query.group_id is None
        assert query.owner_user_email is None

    def test_group_id_alias(self) -> None:
        gid = uuid.uuid4()
        query = ListVFoldersQuery.model_validate({"groupId": str(gid)})
        assert query.group_id == gid

    def test_owner_email_alias(self) -> None:
        query = ListVFoldersQuery.model_validate({"ownerUserEmail": "user@test.com"})
        assert query.owner_user_email == "user@test.com"


class TestListSharedVFoldersQuery:
    def test_defaults(self) -> None:
        query = ListSharedVFoldersQuery.model_validate({})
        assert query.vfolder_id is None

    def test_alias(self) -> None:
        vid = uuid.uuid4()
        query = ListSharedVFoldersQuery.model_validate({"vfolderId": str(vid)})
        assert query.vfolder_id == vid


class TestMkdirReq:
    def test_single_path(self) -> None:
        req = MkdirReq(path="/data/subdir")
        assert req.path == "/data/subdir"
        assert req.parents is True
        assert req.exist_ok is False

    def test_list_paths(self) -> None:
        req = MkdirReq(path=["/a", "/b"])
        assert req.path == ["/a", "/b"]


class TestCreateDownloadSessionReq:
    def test_basic(self) -> None:
        req = CreateDownloadSessionReq(path="/data/file.txt")
        assert req.path == "/data/file.txt"
        assert req.archive is False

    def test_file_alias(self) -> None:
        req = CreateDownloadSessionReq.model_validate({"file": "myfile.bin"})
        assert req.path == "myfile.bin"


class TestCreateUploadSessionReq:
    def test_basic(self) -> None:
        req = CreateUploadSessionReq(path="/uploads/file.txt", size=1024)
        assert req.path == "/uploads/file.txt"
        assert req.size == 1024


class TestRenameFileReq:
    def test_defaults(self) -> None:
        req = RenameFileReq(target_path="/data/old.txt", new_name="new.txt")
        assert req.target_path == "/data/old.txt"
        assert req.new_name == "new.txt"
        assert req.is_dir is False


class TestMoveFileReq:
    def test_basic(self) -> None:
        req = MoveFileReq(src="/a/file.txt", dst="/b/file.txt")
        assert req.src == "/a/file.txt"
        assert req.dst == "/b/file.txt"


class TestDeleteFilesReq:
    def test_basic(self) -> None:
        req = DeleteFilesReq(files=["a.txt", "b.txt"])
        assert req.files == ["a.txt", "b.txt"]
        assert req.recursive is False

    def test_recursive(self) -> None:
        req = DeleteFilesReq(files=["dir/"], recursive=True)
        assert req.recursive is True


class TestDeleteFilesAsyncPathParam:
    def test_basic(self) -> None:
        param = DeleteFilesAsyncPathParam(name="my-vfolder")
        assert param.name == "my-vfolder"


class TestDeleteFilesAsyncBodyParam:
    def test_basic(self) -> None:
        body = DeleteFilesAsyncBodyParam(files=["a.txt", "b.txt"])
        assert body.files == ["a.txt", "b.txt"]
        assert body.recursive is False


class TestListFilesQuery:
    def test_default_path(self) -> None:
        query = ListFilesQuery.model_validate({})
        assert query.path == ""


class TestInviteVFolderReq:
    def test_perm_alias(self) -> None:
        req = InviteVFolderReq.model_validate({"perm": "ro", "emails": ["a@test.com"]})
        assert req.permission == VFolderPermissionField.READ_ONLY
        assert req.emails == ["a@test.com"]

    def test_user_ids_alias(self) -> None:
        req = InviteVFolderReq.model_validate({"permission": "rw", "userIDs": ["a@test.com"]})
        assert req.emails == ["a@test.com"]


class TestAcceptInvitationReq:
    def test_basic(self) -> None:
        req = AcceptInvitationReq(inv_id="abc-123")
        assert req.inv_id == "abc-123"


class TestDeleteInvitationReq:
    def test_basic(self) -> None:
        req = DeleteInvitationReq(inv_id="abc-123")
        assert req.inv_id == "abc-123"


class TestUpdateInvitationReq:
    def test_perm_alias(self) -> None:
        req = UpdateInvitationReq.model_validate({"perm": "ro"})
        assert req.permission == VFolderPermissionField.READ_ONLY


class TestShareVFolderReq:
    def test_defaults(self) -> None:
        req = ShareVFolderReq(emails=["user@test.com"])
        assert req.permission == VFolderPermissionField.READ_WRITE
        assert req.emails == ["user@test.com"]


class TestUnshareVFolderReq:
    def test_basic(self) -> None:
        req = UnshareVFolderReq(emails=["user@test.com"])
        assert req.emails == ["user@test.com"]


class TestUpdateSharedVFolderReq:
    def test_basic(self) -> None:
        vid = uuid.uuid4()
        uid = uuid.uuid4()
        req = UpdateSharedVFolderReq.model_validate({
            "vfolder": str(vid),
            "user": str(uid),
            "perm": "ro",
        })
        assert req.vfolder == vid
        assert req.user == uid
        assert req.permission == VFolderPermissionField.READ_ONLY

    def test_null_permission(self) -> None:
        vid = uuid.uuid4()
        uid = uuid.uuid4()
        req = UpdateSharedVFolderReq(vfolder=vid, user=uid)
        assert req.permission is None


class TestUserPermMapping:
    def test_basic(self) -> None:
        uid = uuid.uuid4()
        mapping = UserPermMapping(user_id=uid, perm=VFolderPermissionField.READ_WRITE)
        assert mapping.user_id == uid
        assert mapping.perm == VFolderPermissionField.READ_WRITE

    def test_null_perm(self) -> None:
        uid = uuid.uuid4()
        mapping = UserPermMapping(user_id=uid)
        assert mapping.perm is None


class TestUpdateVFolderSharingStatusReq:
    def test_basic(self) -> None:
        vid = uuid.uuid4()
        uid = uuid.uuid4()
        req = UpdateVFolderSharingStatusReq.model_validate({
            "vfolder": str(vid),
            "user_perm": [{"user_id": str(uid), "perm": "rw"}],
        })
        assert req.vfolder_id == vid
        assert len(req.user_perm_list) == 1
        assert req.user_perm_list[0].user_id == uid

    def test_alias_userPermList(self) -> None:
        vid = uuid.uuid4()
        uid = uuid.uuid4()
        req = UpdateVFolderSharingStatusReq.model_validate({
            "vfolder": str(vid),
            "userPermList": [{"user_id": str(uid)}],
        })
        assert len(req.user_perm_list) == 1


class TestLeaveVFolderReq:
    def test_defaults(self) -> None:
        req = LeaveVFolderReq.model_validate({})
        assert req.shared_user_uuid is None

    def test_alias(self) -> None:
        req = LeaveVFolderReq.model_validate({"sharedUserUuid": "some-uuid"})
        assert req.shared_user_uuid == "some-uuid"


class TestListHostsQuery:
    def test_defaults(self) -> None:
        query = ListHostsQuery.model_validate({})
        assert query.group_id is None

    def test_alias(self) -> None:
        gid = uuid.uuid4()
        query = ListHostsQuery.model_validate({"groupId": str(gid)})
        assert query.group_id == gid


class TestGetVolumePerfMetricQuery:
    def test_basic(self) -> None:
        query = GetVolumePerfMetricQuery(folder_host="host-1")
        assert query.folder_host == "host-1"


class TestGetQuotaQuery:
    def test_basic(self) -> None:
        qid = uuid.uuid4()
        query = GetQuotaQuery(folder_host="host-1", id=qid)
        assert query.folder_host == "host-1"
        assert query.id == qid


class TestUpdateQuotaReq:
    def test_basic(self) -> None:
        qid = uuid.uuid4()
        req = UpdateQuotaReq(folder_host="host-1", id=qid, input={"size_bytes": 1024})
        assert req.folder_host == "host-1"
        assert req.input == {"size_bytes": 1024}


class TestGetUsageQuery:
    def test_basic(self) -> None:
        qid = uuid.uuid4()
        query = GetUsageQuery(folder_host="host-1", id=qid)
        assert query.id == qid


class TestGetUsedBytesQuery:
    def test_basic(self) -> None:
        qid = uuid.uuid4()
        query = GetUsedBytesQuery(folder_host="host-1", id=qid)
        assert query.id == qid


class TestGetFstabContentsQuery:
    def test_defaults(self) -> None:
        query = GetFstabContentsQuery.model_validate({})
        assert query.fstab_path is None
        assert query.agent_id is None


class TestMountHostReq:
    def test_defaults(self) -> None:
        req = MountHostReq(fs_location="/mnt/nfs", name="nfs-mount")
        assert req.fs_type == "nfs"
        assert req.options is None
        assert req.scaling_group is None
        assert req.edit_fstab is False

    def test_full(self) -> None:
        req = MountHostReq(
            fs_location="/mnt/nfs",
            name="nfs-mount",
            fs_type="ext4",
            options="-o rw",
            scaling_group="sg-1",
            fstab_path="/etc/fstab",
            edit_fstab=True,
        )
        assert req.fs_type == "ext4"
        assert req.edit_fstab is True


class TestUmountHostReq:
    def test_defaults(self) -> None:
        req = UmountHostReq(name="nfs-mount")
        assert req.scaling_group is None
        assert req.edit_fstab is False


class TestChangeVFolderOwnershipReq:
    def test_basic(self) -> None:
        vid = uuid.uuid4()
        req = ChangeVFolderOwnershipReq(vfolder=vid, user_email="new@owner.com")
        assert req.vfolder == vid
        assert req.user_email == "new@owner.com"
