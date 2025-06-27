import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.templates.vfolder.general_vfolder import GeneralVFolderTemplate
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.testcases.vfolder.restore import VFolderDeleteAndRestoreSuccess

VFOLDER_TEST_SPECS = {
    "restore_vfolder": TestSpec(
        name="restore_vfolder",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create a vfolder with a specified name and resources.
            2. Delete the vfolder.
            3. Restore the vfolder from the deleted state.
            4. Verify that the vfolder is restored and available.
            5. Clean up the vfolder after verification.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderDeleteAndRestoreSuccess()).with_wrappers(
            KeypairAuthTemplate, GeneralVFolderTemplate
        ),
    ),
}
