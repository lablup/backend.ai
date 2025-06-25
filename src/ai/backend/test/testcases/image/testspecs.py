import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.image.rescan import ImageRescanTemplate
from ai.backend.test.testcases.image.rescan_comparison import RescanResultComparison
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

from ...templates.template import BasicTestTemplate

IMAGE_RESCAN_TEST_SPECS = {
    "harbor_v2_image_rescan_success": TestSpec(
        name="harbor_v2_image_rescan_success",
        description=textwrap.dedent("""\
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.IMAGE},
        template=BasicTestTemplate(RescanResultComparison()).with_wrappers(
            KeypairAuthTemplate, ImageRescanTemplate
        ),
    ),
}
