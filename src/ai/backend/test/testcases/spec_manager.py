import enum
import textwrap
from dataclasses import dataclass
from itertools import product
from typing import Any, Mapping, Optional, Sequence

from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.template import (
    BasicTestTemplate,
    TestTemplate,
)
from ai.backend.test.testcases.session.create_multi_node_multi_container_session import (
    MultiNodeMultiContainerSessionCreation,
)
from ai.backend.test.testcases.session.create_single_node_multi_container_session import (
    SingleNodeMultiContainerSessionCreation,
)
from ai.backend.test.testcases.session.create_single_node_single_container_session import (
    SingleNodeSingleContainerSessionCreation,
)
from ai.backend.test.testcases.session.destroy_session import DestroySession
from ai.backend.test.testcases.session.template import (
    SessionLifecycleTemplate,
    SessionNameTemplateWrapper,
)


class TestTag(enum.StrEnum):
    # component based tags
    MANAGER = "manager"
    AGENT = "agent"
    WEBSERVER = "webserver"

    # Domain specific tags
    AUTH = "auth"
    VFOLDER = "vfolder"
    IMAGE = "image"
    SESSION = "session"


@dataclass
class TestSpec:
    name: str
    description: str
    tags: set[TestTag]
    template: TestTemplate
    parametrizes: Optional[Mapping[ContextName, Sequence[Any]]] = None

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, TestSpec):
            return NotImplemented
        # If name is the same, consider them equal
        return self.name == other.name

    def product_parametrizes(self) -> Optional[Sequence[Mapping[ContextName, Any]]]:
        """
        Get the product of all parametrizes for the test specification.
        """
        if not self.parametrizes:
            return None
        keys = list(self.parametrizes.keys())
        values_product = product(*(self.parametrizes[key] for key in keys))
        return [dict(zip(keys, combination)) for combination in values_product]


class TestSpecManager:
    _specs: Mapping[str, TestSpec]

    def __init__(self, specs: Mapping[str, TestSpec]) -> None:
        self._specs = specs

    @classmethod
    def default(cls) -> Self:
        specs = {
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
                        BasicTestTemplate(SingleNodeSingleContainerSessionCreation()),
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
                        BasicTestTemplate(SingleNodeMultiContainerSessionCreation()),
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
                        BasicTestTemplate(MultiNodeMultiContainerSessionCreation()),
                        BasicTestTemplate(DestroySession()),
                    ])
                ),
            ),
        }
        return cls(specs)

    def all_specs(self) -> set[TestSpec]:
        """
        Get all test specifications.
        """
        return set(self._specs.values())

    def specs_by_tag(self, tag: TestTag) -> set[TestSpec]:
        """
        Get test specifications by tag.
        """
        return {spec for spec in self._specs.values() if tag in spec.tags}

    def spec_by_name(self, name: str) -> TestSpec:
        """
        Get test specifications by name.
        """
        if name not in self._specs:
            raise KeyError(f"Test specification '{name}' not found.")
        return self._specs[name]
