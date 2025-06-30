import textwrap

from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.templates.vfolder.file_uploader import PlainTextFilesUploader
from ai.backend.test.templates.vfolder.general_vfolder import GeneralVFolderTemplate
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.testcases.vfolder.clone import VFolderCloneSuccess
from ai.backend.test.tester.dependency import UploadFileDep

_TEST_FILE_CONTENT = "This is a test file for VFolder download."

VFOLDER_TEST_SPECS = {
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
                        path="nested/test_3.txt",
                        content=_TEST_FILE_CONTENT,
                    ),
                ]
            ]
        },
    ),
}
