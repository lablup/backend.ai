import enum
from dataclasses import dataclass
from typing import Mapping

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
    SESSION = "session"


@dataclass
class TestSpec:
    name: str
    description: str
    tags: set[TestTag]
    template: TestTemplate

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, TestSpec):
            return NotImplemented
        # If name is the same, consider them equal
        return self.name == other.name


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
