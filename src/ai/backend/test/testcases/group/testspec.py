import textwrap

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.group.add_group_to_user import AddGroupToKeypairTemplate
from ai.backend.test.templates.group.group import GroupTemplate
from ai.backend.test.templates.model_service.endpoint import (
    CustomGroupEndpointTemplate,
)
from ai.backend.test.templates.session.interactive_session import (
    InteractiveSessionWithCustomGroupTemplate,
)
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.group.purge_group_fail_remaining_endpoint import (
    PurgeGroupFailRemainingActiveEndpointExist,
    PurgeGroupFailRemainingActiveSessionExist,
)
from ai.backend.test.testcases.group.purge_group_success import PurgeGroupSuccess
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.tester.dependency import ClusterDep

GROUP_TEST_SPEC = {
    "purge_group_fail_remaining_active_endpoint_exist": TestSpec(
        name="purge_group_fail_remaining_active_endpoint_exist",
        description=textwrap.dedent("""\
            Test for purging a group with remaining active endpoints.
            This test verifies that purging a group fails when there are active endpoints associated with it.
            The test will:
            1. Create a group and an endpoint within that group.
            2. Attempt to purge the group.
            3. Assert that the purge operation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.GROUP},
        template=BasicTestTemplate(PurgeGroupFailRemainingActiveEndpointExist()).with_wrappers(
            KeypairAuthTemplate,
            GroupTemplate,
            AddGroupToKeypairTemplate,
            CustomGroupEndpointTemplate,
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ],
        },
    ),
    "purge_group_fail_remaining_active_session_exist": TestSpec(
        name="purge_group_fail_remaining_active_session_exist",
        description=textwrap.dedent("""\
            Test for purging a group with remaining active sessions.
            This test verifies that purging a group fails when there are active sessions associated with it.
            The test will:
            1. Create a group and a session within that group.
            2. Attempt to purge the group.
            3. Assert that the purge operation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.GROUP},
        template=BasicTestTemplate(PurgeGroupFailRemainingActiveSessionExist()).with_wrappers(
            KeypairAuthTemplate,
            GroupTemplate,
            AddGroupToKeypairTemplate,
            InteractiveSessionWithCustomGroupTemplate,
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ],
        },
    ),
    "purge_group_success": TestSpec(
        name="purge_group_success",
        description=textwrap.dedent("""\
            Test for successfully purging a group.
            This test verifies that a group can be purged successfully when there are no active endpoints or sessions.
            The test will:
            1. Create a group.
            2. Purge the group.
            3. Assert that the group is no longer listed in the system.
        """),
        tags={TestTag.MANAGER, TestTag.GROUP},
        template=BasicTestTemplate(PurgeGroupSuccess()).with_wrappers(
            KeypairAuthTemplate,
            GroupTemplate,
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ],
        },
    ),
}
