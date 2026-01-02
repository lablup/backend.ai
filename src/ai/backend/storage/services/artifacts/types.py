from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from ai.backend.common.artifact_storage import AbstractStorage, ImportStepContext
from ai.backend.common.data.artifact.types import ArtifactRegistryType, VerificationStepResult
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
    verification_result: VerificationStepResult


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

    @property
    @abc.abstractmethod
    def registry_type(self) -> ArtifactRegistryType:
        """Return the registry type for this step (used for revision resolution)"""
        pass

    @abc.abstractmethod
    def stage_storage(self, context: ImportStepContext) -> AbstractStorage:
        """Return the storage for this step"""
        pass

    async def cleanup_stage(self, context: ImportStepContext) -> None:
        """Default cleanup implementation that removes files"""
        storage = self.stage_storage(context)
        revision = context.model.resolve_revision(self.registry_type)
        model_prefix = f"{context.model.model_id}/{revision}"

        try:
            await storage.delete_file(model_prefix)
            log.info(f"[cleanup] Removed files: {model_prefix}")
        except Exception as e:
            log.warning(f"[cleanup] Failed to cleanup: {model_prefix}: {str(e)}")


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
