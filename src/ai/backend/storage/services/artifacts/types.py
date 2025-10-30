from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from ai.backend.common.artifact_storage import ImportStepContext
from ai.backend.common.data.storage.registries.types import FileObjectData
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


@dataclass
class DownloadStepResult:
    """Result of download step"""

    downloaded_files: list[tuple[FileObjectData, str]]  # (file_info, storage_key)
    storage_name: str
    total_bytes: int


@dataclass
class VerifyStepResult:
    """Result of verify step"""

    verified_files: list[tuple[FileObjectData, str]]  # (file_info, storage_key)
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
    async def cleanup_stage(self, context: ImportStepContext) -> None:
        """Perform cleanup after stage completion, or after failure"""
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

            # On success, cleanup all non-archive steps
            archive_storage = context.storage_step_mappings.get(ArtifactStorageImportStep.ARCHIVE)

            for step in completed_steps:
                if step.step_type != ArtifactStorageImportStep.ARCHIVE:
                    step_storage = context.storage_step_mappings.get(step.step_type)

                    # Skip cleanup if this step uses the same storage as archive step
                    if step_storage == archive_storage:
                        continue

                    try:
                        await step.cleanup_stage(context)
                    except Exception:
                        log.error(f"Failed to cleanup step {step.step_type}")
                        pass

        except Exception:
            # Cleanup completed steps in reverse order on failure
            for step in reversed(completed_steps):
                try:
                    await step.cleanup_stage(context)
                except Exception:
                    # Log cleanup failures but continue with other cleanups
                    log.error(f"Failed to cleanup step {step.step_type}")
                    pass
            raise
