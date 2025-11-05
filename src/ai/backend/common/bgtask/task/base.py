from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

from ..types import BgtaskNameBase


class BaseBackgroundTaskManifest(BaseModel):
    """
    Base class for background task manifests using Pydantic.
    Provides automatic serialization/deserialization via model_dump() and model_validate().
    """

    model_config = ConfigDict(
        # Allow custom types in manifests
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )


class BaseBackgroundTaskResult(BaseModel):
    """
    Base class for background task results using Pydantic.
    Provides automatic serialization/deserialization via model_dump() and model_validate().
    """

    model_config = ConfigDict(
        # Allow custom types in results (e.g., UUID, custom domain types)
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )


TManifest = TypeVar("TManifest", bound=BaseBackgroundTaskManifest)
TResult = TypeVar("TResult", bound=Optional[BaseBackgroundTaskResult])


class BaseBackgroundTaskHandler(Generic[TManifest, TResult], ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> BgtaskNameBase:
        """
        Return the name of the background task.
        This method should be implemented by subclasses to provide
        the specific task name.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def manifest_type(cls) -> type[TManifest]:
        """
        Return the type of manifest that this task expects.
        This method should be implemented by subclasses to provide
        the specific manifest type.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def execute(self, manifest: TManifest) -> TResult:
        """
        Execute the background task with the provided manifest.
        Returns the result or None if no meaningful result is produced.
        This method should be implemented by subclasses to provide
        the specific execution logic.
        """
        raise NotImplementedError("Subclasses must implement this method")
