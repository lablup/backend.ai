from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import Optional

from ai.backend.common.data.storage.registries.types import ModelTarget


class ArtifactStorageType(enum.StrEnum):
    OBJECT_STORAGE = "object_storage"
    VFS = "vfs"
    GIT_LFS = "git_lfs"


class ArtifactStorageImportStep(enum.Enum):
    DOWNLOAD = "download"
    VERIFY = "verify"
    ARCHIVE = "archive"


class StorageSelectionStrategy(ABC):
    """Abstract base class for storage selection strategies."""

    @abstractmethod
    async def select_storage(
        self,
        step: ArtifactStorageImportStep,
        model: ModelTarget,
        context: dict,
    ) -> str:
        """
        Select appropriate storage for the given import step.

        Args:
            step: The import step (download, verify, archive)
            model: Model target information
            context: Additional context for selection decision

        Returns:
            Storage name to use for this step
        """
        pass


class ConfigBasedSelectionStrategy(StorageSelectionStrategy):
    """Storage selection strategy based on configuration mapping."""

    def __init__(self, step_mappings: dict[ArtifactStorageImportStep, str]):
        self._step_mappings = step_mappings

    async def select_storage(
        self,
        step: ArtifactStorageImportStep,
        model: ModelTarget,
        context: dict,
    ) -> str:
        if step not in self._step_mappings:
            # TODO: Add new exception type
            raise ValueError(f"No storage mapping configured for step: {step}")

        return self._step_mappings[step]


class StorageSelectionMiddleware:
    """Middleware for selecting appropriate storage at each import step."""

    def __init__(self, strategy: StorageSelectionStrategy):
        self._strategy = strategy

    async def get_storage_for_step(
        self,
        step: ArtifactStorageImportStep,
        model: ModelTarget,
        context: Optional[dict] = None,
    ) -> str:
        """
        Get storage name for the specified import step.

        Args:
            step: The import step
            model: Model target information
            context: Additional context for selection

        Returns:
            Storage name to use
        """
        return await self._strategy.select_storage(step, model, context or {})

    @classmethod
    def from_config(cls, config) -> StorageSelectionMiddleware:
        """
        Create storage selection middleware from configuration.

        Args:
            config: Storage selection configuration

        Returns:
            Configured StorageSelectionMiddleware instance
        """
        # Convert string keys to ImportStep enums
        step_mappings = {}
        for step_name, storage_name in config.storage_mappings.items():
            try:
                step = ArtifactStorageImportStep(step_name)
                step_mappings[step] = storage_name
            except ValueError:
                # Skip unknown step names
                continue

        strategy = ConfigBasedSelectionStrategy(step_mappings)
        return cls(strategy)
