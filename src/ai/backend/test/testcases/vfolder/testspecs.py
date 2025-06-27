import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.templates.vfolder.general_vfolder import GeneralVFolderTemplate
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.testcases.vfolder.download import VFolderDownloadSuccess

VFOLDER_TEST_SPECS = {
    "upload_and_download_files_vfolder": TestSpec(
        name="upload_and_download_files_vfolder",
        description=textwrap.dedent("""\
            Test for uploading and downloading files in a VFolder.
            The test will:
            1. Create a VFolder.
            2. Upload files to the VFolder.
            3. Download the files from the VFolder.
            4. Verify that the downloaded files match the uploaded files.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderDownloadSuccess()).with_wrappers(
            KeypairAuthTemplate, GeneralVFolderTemplate
        ),
    ),
}
