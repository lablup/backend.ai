import textwrap

from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.templates.vfolder.file_uploader import PlainTextFilesUploader
from ai.backend.test.templates.vfolder.general_vfolder import GeneralVFolderTemplate
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.testcases.vfolder.download import VFolderDownloadSuccess
from ai.backend.test.tester.dependency import UploadFileDep

_TEST_FILE_CONTENT = "This is a test file for VFolder download."

VFOLDER_TEST_SPECS = {
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
