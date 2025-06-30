import textwrap

from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.templates.vfolder.file_uploader import PlainTextFilesUploader
from ai.backend.test.templates.vfolder.general_vfolder import GeneralVFolderTemplate
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.testcases.vfolder.clone import VFolderCloneSuccess
from ai.backend.test.testcases.vfolder.delete_files import (
    VFolderFilesDeletionSuccess,
    VFolderFilesRecursiveDeletionSuccess,
)
from ai.backend.test.testcases.vfolder.download import VFolderDownloadSuccess
from ai.backend.test.testcases.vfolder.list_files import VFolderListFilesSuccess
from ai.backend.test.testcases.vfolder.move import VFolderFileMoveSuccess
from ai.backend.test.testcases.vfolder.rename_file import VFolderFileRenameSuccess
from ai.backend.test.tester.dependency import UploadFileDep

_TEST_FILE_CONTENT = "This is a test file for VFolder download."

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
            KeypairAuthTemplate, GeneralVFolderTemplate, PlainTextFilesUploader
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
            KeypairAuthTemplate, GeneralVFolderTemplate, PlainTextFilesUploader
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
            KeypairAuthTemplate, GeneralVFolderTemplate, PlainTextFilesUploader
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
            KeypairAuthTemplate, GeneralVFolderTemplate, PlainTextFilesUploader
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
            KeypairAuthTemplate, GeneralVFolderTemplate, PlainTextFilesUploader
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
            KeypairAuthTemplate, GeneralVFolderTemplate, PlainTextFilesUploader
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
}
