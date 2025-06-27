import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.templates.vfolder.general_vfolder import GeneralVFolderTemplate
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.testcases.vfolder.purge import VFolderPurgeSuccess
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
    "purge_vfolder": TestSpec(
        name="purge_vfolder",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create a vfolder with a specified name and resources.
            2. Attempt to purge the vfolder before deletion (should fail).
            3. Delete the vfolder.
            4. Verify that the vfolder is in a soft-deleted state.
            5. Purge the vfolder.
            6. Verify that the vfolder is no longer retrievable.
        """),
        tags={TestTag.MANAGER, TestTag.VFOLDER},
        template=BasicTestTemplate(VFolderPurgeSuccess()).with_wrappers(
            KeypairAuthTemplate,
        ),
    ),
}
