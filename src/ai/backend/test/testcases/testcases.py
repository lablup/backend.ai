import enum
from abc import ABC, abstractmethod
from typing import Mapping, Self


class TestTag(enum.StrEnum):
    # component based tags
    MANAGER = "manager"
    AGENT = "agent"

    # Domain specific tags
    VFOLDER = "vfolder"
    IMAGE = "image"
    SESSION = "session"


class TestSpec(ABC):
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the test specification.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the test specification.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def tags(self) -> set[TestTag]:
        """
        Get the tags associated with the test specification.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def run_test(self) -> None:
        """
        Run the test case associated with this specification.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class NopTestSpec(TestSpec):
    def name(self) -> str:
        return "nop"

    def description(self) -> str:
        return "A no-operation test specification for testing purposes."

    def tags(self) -> set[TestTag]:
        return {TestTag.MANAGER}

    async def run_test(self) -> None:
        pass


class TestSpecManager:
    _specs: Mapping[str, TestSpec]

    def __init__(self, specs: Mapping[str, TestSpec]) -> None:
        self._specs = specs

    @classmethod
    def default(cls) -> Self:
        specs = {"nop": NopTestSpec()}
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
        return {spec for spec in self._specs.values() if tag in spec.tags()}

    def spec_by_name(self, name: str) -> TestSpec:
        """
        Get test specifications by name.
        """
        if name not in self._specs:
            raise KeyError(f"Test specification '{name}' not found.")
        return self._specs[name]
