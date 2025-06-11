import textwrap

from ai.backend.common.types import ClusterMode

from ...templates.template import BasicTestTemplate
from ..testcases import TestSpec, TestTag
from .create_session import (
    CreateSession,
    CreateSessionArgs,
)
from .destroy_session import DestroySession
from .template import (
    SessionLifecycleTemplate,
    SessionNameTemplateWrapper,
)

SESSION_TEST_SPECS = {
    "single_node_single_container_session": TestSpec(
        name="single_node_single_container_session",
        description=textwrap.dedent("""\
            Test for creating a single-node, single-container session.
            This test verifies that a session can be created with a single node and a single container, and that it transitions through the expected lifecycle events.

            The test will:
            1. Create a session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is running after creation.
            4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=SessionNameTemplateWrapper(
            SessionLifecycleTemplate([
                BasicTestTemplate(
                    CreateSession(
                        CreateSessionArgs(cluster_mode=ClusterMode.SINGLE_NODE, cluster_size=1)
                    )
                ),
                BasicTestTemplate(DestroySession()),
            ])
        ),
    ),
    "single_node_multi_container_session": TestSpec(
        name="single_node_multi_container_session",
        description=textwrap.dedent("""\
            Test for creating a single-node, multi-container session.
            This test verifies that a session can be created with a single node and multiple containers, and that it transitions through the expected lifecycle events.

            The test will:
            1. Create a session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is running after creation.
            4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=SessionNameTemplateWrapper(
            SessionLifecycleTemplate([
                BasicTestTemplate(
                    CreateSession(
                        CreateSessionArgs(cluster_mode=ClusterMode.SINGLE_NODE, cluster_size=3)
                    )
                ),
                BasicTestTemplate(DestroySession()),
            ])
        ),
    ),
    "multi_node_multi_container_session": TestSpec(
        name="multi_node_multi_container_session",
        description=textwrap.dedent("""\
            Test for creating a multi-node, multi-container session.
            This test verifies that a session can be created with multiple nodes and multiple containers, and that it transitions through the expected lifecycle events.

            The test will:
            1. Create a session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is running after creation.
            4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=SessionNameTemplateWrapper(
            SessionLifecycleTemplate([
                BasicTestTemplate(
                    CreateSession(
                        CreateSessionArgs(cluster_mode=ClusterMode.MULTI_NODE, cluster_size=3)
                    )
                ),
                BasicTestTemplate(DestroySession()),
            ])
        ),
    ),
}
