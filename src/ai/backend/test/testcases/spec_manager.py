import enum
from dataclasses import dataclass
from itertools import product
from typing import Any, Mapping, Optional, Sequence

from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.template import (
    TestTemplate,
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
    CONTAINER_REGISTRY = "container_registry"
    SESSION = "session"
    MODEL_SERVICE = "model_service"
    GROUP = "group"

    # Need extra configuration to pass these tests
    REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION = (
        "required_single_node_multi_container_configuration"
    )
    REQUIRED_MULTI_NODE_MULTI_CONTAINER_CONFIGURATION = (
        "required_multi_node_multi_container_configuration"
    )
    REQUIRED_CONTAINER_REGISTRY_CONFIGURATION = "required_container_registry_configuration"

    # Others
    LONG_RUNNING = "long_running"
    SINGLE_NODE_SINGLE_CONTAINER = "single_node_single_container"


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
