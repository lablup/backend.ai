import textwrap

from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import (
    KeypairAuthAsCreatedUserTemplate,
    KeypairAuthTemplate,
)
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.templates.user.user import UserTemplate
from ai.backend.test.templates.vfolder.file_uploader import PlainTextFilesUploader
from ai.backend.test.templates.vfolder.general_vfolder import (
    ProjectVFolderTemplate,
    UserVFolderTemplate,
)
from ai.backend.test.templates.vfolder.invite import (
    AcceptInvitationTemplate,
    RejectInvitationTemplate,
    VFolderInviteTemplate,
)
from ai.backend.test.templates.vfolder.share import ShareVFolderTemplate
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.testcases.vfolder.access import VFolderAccessFailure, VFolderAccessSuccess
from ai.backend.test.testcases.vfolder.clone import VFolderCloneSuccess
from ai.backend.test.testcases.vfolder.delete_files import (
    VFolderFilesDeletionSuccess,
    VFolderFilesRecursiveDeletionSuccess,
)
from ai.backend.test.testcases.vfolder.download import VFolderDownloadSuccess
from ai.backend.test.testcases.vfolder.invite_failures import (
    VFolderAcceptDuplicatedInvitation,
    VFolderInviteFailure,
)
from ai.backend.test.testcases.vfolder.list_files import VFolderListFilesSuccess
from ai.backend.test.testcases.vfolder.move import VFolderFileMoveSuccess
from ai.backend.test.testcases.vfolder.rename_file import VFolderFileRenameSuccess
from ai.backend.test.testcases.vfolder.share import VFolderSharePermissionOverrideSuccess
from ai.backend.test.tester.dependency import UploadFileDep

_TEST_FILE_CONTENT = "This is a test file for VFolder download."

VFOLDER_INVITATION_TEST_SPECS = {
    "invite_vfolder_success": TestSpec(
        name="invite_vfolder_success",
        description=textwrap.dedent("""\
            Test for VFolder invitation functionality.
            The test will:
            1. Authenticate as admin and create a VFolder.
            2. Create a test user.
            3. Invite the test user to the VFolder.
            4. Login as the test user.
            5. Accept the VFolder invitation.
            6. Verify that the test user can access the VFolder.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderAccessSuccess()).with_wrappers(
            # Run as admin
            KeypairAuthTemplate,
            UserVFolderTemplate,
            UserTemplate,
            VFolderInviteTemplate,
            # Run as invitee user
            KeypairAuthAsCreatedUserTemplate,
            AcceptInvitationTemplate,
        ),
        parametrizes={
            ContextName.VFOLDER_INVITATION_PERMISSION: ["rw", "ro"],
        },
    ),
    "invite_vfolder_failure_reject": TestSpec(
        name="invite_vfolder_failure_reject",
        description=textwrap.dedent("""\
            Test for VFolder invitation functionality.
            The test will:
            1. Authenticate as admin and create a VFolder.
            2. Create a test user.
            3. Invite the test user to the VFolder.
            4. Login as the test user.
            5. Reject the VFolder invitation.
            6. Verify that the test user cannot access the VFolder.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderAccessFailure()).with_wrappers(
            # Run as admin
            KeypairAuthTemplate,
            UserVFolderTemplate,
            UserTemplate,
            VFolderInviteTemplate,
            # Run as invitee user
            KeypairAuthAsCreatedUserTemplate,
            RejectInvitationTemplate,
        ),
        parametrizes={
            ContextName.VFOLDER_INVITATION_PERMISSION: ["rw", "ro"],
        },
    ),
    "invite_vfolder_failure_duplicated_accept": TestSpec(
        name="invite_vfolder_failure_duplicated_accept",
        description=textwrap.dedent("""\
            Test for VFolder invitation functionality.
            The test will:
            1. Authenticate as admin and create a VFolder.
            2. Create a test user.
            3. Invite the test user to the VFolder.
            4. Login as the test user.
            5. Accept the VFolder invitation.
            6. Try to accept the same invitation again.
            7. Verify that the second acceptance fails with an error.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderAcceptDuplicatedInvitation()).with_wrappers(
            # Run as admin
            KeypairAuthTemplate,
            UserVFolderTemplate,
            UserTemplate,
            VFolderInviteTemplate,
            # Run as invitee user
            KeypairAuthAsCreatedUserTemplate,
        ),
        parametrizes={
            ContextName.VFOLDER_INVITATION_PERMISSION: ["rw"],
        },
    ),
    "invite_vfolder_failure_duplicated_invitation": TestSpec(
        name="invite_vfolder_failure_duplicated_invitation",
        description=textwrap.dedent("""\
            Test for VFolder invitation functionality.
            The test will:
            1. Authenticate as admin and create a VFolder.
            2. Create a test user.
            3. Invite the test user to the VFolder.
            4. Login as the test user.
            5. Accept the VFolder invitation.
            6. Try to invite the same user again to the same VFolder.
            7. Verify that the second invitation fails with an error.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderInviteFailure()).with_wrappers(
            # Run as admin
            KeypairAuthTemplate,
            UserVFolderTemplate,
            UserTemplate,
            VFolderInviteTemplate,
            # Run as invitee user
            KeypairAuthAsCreatedUserTemplate,
            AcceptInvitationTemplate,
        ),
        parametrizes={
            ContextName.VFOLDER_INVITATION_PERMISSION: ["rw"],
        },
    ),
}

VFOLDER_TEST_SPECS = {
    "list_files": TestSpec(
        name="list_files",
        description=textwrap.dedent("""\
            Test for renaming a file in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. List files in the VFolder.
            4. Verify that the files are listed correctly.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderListFilesSuccess()).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, PlainTextFilesUploader
        ),
        parametrizes={
            ContextName.VFOLDER_UPLOAD_FILES: [
                [
                    UploadFileDep(
                        path="test_1.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="test_2.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="test_3.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
    "rename_file": TestSpec(
        name="rename_file",
        description=textwrap.dedent("""\
            Test for renaming a file in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. Rename a file in the VFolder.
            4. Verify that the file has been renamed successfully.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderFileRenameSuccess()).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, PlainTextFilesUploader
        ),
        parametrizes={
            ContextName.VFOLDER_UPLOAD_FILES: [
                [
                    UploadFileDep(
                        path="file.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
    "move_file": TestSpec(
        name="move_file",
        description=textwrap.dedent("""\
            Test for renaming a file in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. Move a file in the VFolder.
            4. Verify that the file has been moved successfully.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderFileMoveSuccess()).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, PlainTextFilesUploader
        ),
        parametrizes={
            ContextName.VFOLDER_UPLOAD_FILES: [
                [
                    UploadFileDep(
                        path="file.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
    "delete_files": TestSpec(
        name="delete_files",
        description=textwrap.dedent("""\
            Test for renaming a file in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. Delete some files in the VFolder.
            4. Verify that the files have been deleted successfully.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderFilesDeletionSuccess()).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, PlainTextFilesUploader
        ),
        parametrizes={
            ContextName.VFOLDER_UPLOAD_FILES: [
                [
                    UploadFileDep(
                        path="test_1.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="test_2.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="test_3.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
    "delete_files_recursively": TestSpec(
        name="delete_files_recursively",
        description=textwrap.dedent("""\
            Test for renaming a file in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. Delete some files in the VFolder recursively.
            4. Verify that the files have been deleted successfully.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderFilesRecursiveDeletionSuccess("nested")).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, PlainTextFilesUploader
        ),
        parametrizes={
            ContextName.VFOLDER_UPLOAD_FILES: [
                [
                    UploadFileDep(
                        path="nested/test_1.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="nested/test_2.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="nested/inner_nested/test_3.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
    "download_files": TestSpec(
        name="download_files",
        description=textwrap.dedent("""\
            Test for downloading files in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. Download the files from the VFolder.
            4. Verify that the downloaded files match the uploaded files.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderDownloadSuccess()).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, PlainTextFilesUploader
        ),
        parametrizes={
            ContextName.VFOLDER_UPLOAD_FILES: [
                [
                    UploadFileDep(
                        path="test_1.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="test_2.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="test_3.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="nested/inner.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
    "clone_vfolder": TestSpec(
        name="clone_vfolder",
        description=textwrap.dedent("""\
            Test for renaming a file in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. Clone the VFolder.
            4. Verify that the files in the cloned VFolder match the original VFolder.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderCloneSuccess()).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, PlainTextFilesUploader
        ),
        parametrizes={
            ContextName.VFOLDER_UPLOAD_FILES: [
                [
                    UploadFileDep(
                        path="test_1.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="test_2.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                    UploadFileDep(
                        path="nested/test_3.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
    "shared_vfolder_permission_override": TestSpec(
        name="shared_vfolder_permission_override",
        description=textwrap.dedent("""\
            Test for VFolder sharing functionality.
            The test will:
            1. Authenticate as admin and create a VFolder.
            2. Create a test user.
            3. Share the VFolder with the test user.
            4. Login as the test user.
            5. Verify that the test user can access the VFolder with the shared permission.
            6. Unshare the VFolder from the test user.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderSharePermissionOverrideSuccess()).with_wrappers(
            # Run as admin(sharing user)
            KeypairAuthTemplate,
            ProjectVFolderTemplate,
            UserTemplate,
            ShareVFolderTemplate,
            # Run as shared user
            KeypairAuthAsCreatedUserTemplate,
        ),
    ),
    **VFOLDER_INVITATION_TEST_SPECS,
}
