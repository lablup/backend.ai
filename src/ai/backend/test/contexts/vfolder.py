from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.vfolder import (
    UploadedFilesMeta,
    VFolderInvitationMeta,
    VFolderMeta,
    VFolderShareMeta,
)
from ai.backend.test.tester.dependency import UploadFileDep, VFolderDep


class VFolderContext(BaseTestContext[VFolderDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER


class CreatedVFolderMetaContext(BaseTestContext[VFolderMeta]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_VFOLDER_META


class UploadFilesContext(BaseTestContext[list[UploadFileDep]]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER_UPLOAD_FILES


class UploadedFilesContext(BaseTestContext[UploadedFilesMeta]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER_UPLOADED_FILES_META


class VFolderInvitationContext(BaseTestContext[VFolderInvitationMeta]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER_INVITATION


# TODO: Move the VFolderPermission type to the common package and use VFolderPermission instead of str.
class VFolderInvitationPermissionContext(BaseTestContext[str]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER_INVITATION_PERMISSION


class VFolderShareContext(BaseTestContext[VFolderShareMeta]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER_SHARE_META
