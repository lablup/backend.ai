from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from ai.backend.common.bgtask.bgtask import ProgressReporter
from ai.backend.common.data.storage.registries.types import FileObjectData, ModelTarget
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.storage.storages.storage_pool import StoragePool


@dataclass
class ImportStepContext:
    """Context shared across import steps"""

    model: ModelTarget
    registry_name: str
    storage_pool: StoragePool
    progress_reporter: Optional[ProgressReporter]
    storage_step_mappings: dict[ArtifactStorageImportStep, str]
    step_metadata: dict[str, Any]  # For passing data between steps


@dataclass
class DownloadStepResult:
    """Result of download step"""

    downloaded_files: list[tuple[FileObjectData, str]]  # (file_info, storage_key)
    storage_name: str
    total_bytes: int


InputType = TypeVar("InputType")


class ImportStep(abc.ABC, Generic[InputType]):
    """Base class for import pipeline steps"""

    @property
    @abc.abstractmethod
    def step_type(self) -> ArtifactStorageImportStep:
        """Return the type of this step"""
        pass

    @abc.abstractmethod
    async def execute(self, context: ImportStepContext, input_data: InputType) -> Any:
        """Execute step and return data to pass to next step"""
        pass

    @abc.abstractmethod
    async def cleanup_on_failure(self, context: ImportStepContext) -> None:
        """Perform cleanup on failure"""
        pass


class ImportPipeline:
    """Pipeline that executes import steps in sequence"""

    def __init__(self, steps: list[ImportStep[Any]]) -> None:
        self._steps = steps

    async def execute(self, context: ImportStepContext) -> None:
        """Execute all pipeline steps in sequence"""
        completed_steps: list[ImportStep[Any]] = []
        try:
            current_data: Any = None

            for step in self._steps:
                current_data = await step.execute(context, current_data)
                completed_steps.append(step)

        except Exception:
            # Cleanup completed steps in reverse order on failure
            for step in reversed(completed_steps):
                try:
                    await step.cleanup_on_failure(context)
                except Exception:
                    # Log cleanup failures but continue with other cleanups
                    pass
            raise
