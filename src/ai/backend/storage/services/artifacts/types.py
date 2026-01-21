from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from ai.backend.common.artifact_storage import AbstractStorage
from ai.backend.common.data.artifact.types import ArtifactRegistryType, VerificationStepResult
from ai.backend.common.data.storage.registries.types import FileObjectData
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.data.storage.types import ImportStepContext

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

    def _resolve_storage_prefix(self, context: ImportStepContext, default_prefix: str) -> str:
        """
        Resolve storage prefix based on storage_prefix setting.

        Args:
            context: Import step context containing storage_prefix
            default_prefix: Default prefix when storage_prefix is None


        Returns:
            The resolved prefix ("/" for root storage)
        """
        if context.custom_storage_prefix is None:
            return default_prefix
        return context.custom_storage_prefix

    def _resolve_storage_key(
        self, context: ImportStepContext, default_prefix: str, file_path: str
    ) -> str:
        """
        Resolve full storage key for a file based on storage_prefix setting.

        Args:
            context: Import step context containing storage_prefix
            default_prefix: Default prefix when storage_prefix is None
            file_path: The file path to store

        Returns:
            The resolved storage key path
        """
        prefix = self._resolve_storage_prefix(context, default_prefix)
        # "/" means root storage - store files without prefix
        if prefix == "/":
            return file_path
        if prefix:
            return f"{prefix}/{file_path}"
        return file_path

    async def cleanup_stage(self, context: ImportStepContext) -> None:
        """Default cleanup implementation that removes files"""
        storage = self.stage_storage(context)
        revision = context.model.resolve_revision(self.registry_type)
        model_prefix = f"{context.model.model_id}/{revision}"

        try:
            await storage.delete_file(model_prefix)
            log.info(f"[cleanup] Removed files: {model_prefix}")
        except Exception as e:
            log.warning(f"[cleanup] Failed to cleanup: {model_prefix}: {e!s}")


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
