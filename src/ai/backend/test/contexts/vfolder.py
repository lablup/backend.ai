from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.vfolder import UploadedFilesMeta, VFolderInvitationMeta, VFolderMeta
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


class VFolderInvitationPermissionContext(BaseTestContext[str]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER_INVITATION_PERMISSION
