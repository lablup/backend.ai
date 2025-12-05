from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ai.backend.common.artifact_storage import AbstractStorage, ImportStepContext
from ai.backend.common.data.artifact.types import ArtifactRegistryType, VerificationStepResult
from ai.backend.common.data.storage.registries.types import FileObjectData
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.storage.storages.vfs_storage import VFSStorage

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
        """Default cleanup implementation that removes files and empty parent directories"""
        from ai.backend.storage.storages.vfs_storage import VFSStorage

        storage = self.stage_storage(context)
        revision = context.model.resolve_revision(self.registry_type)
        model_prefix = f"{context.model.model_id}/{revision}"
        model_id = context.model.model_id

        try:
            await storage.delete_file(model_prefix)
            log.info(f"[cleanup] Removed files: {model_prefix}")
        except Exception as e:
            log.warning(f"[cleanup] Failed to cleanup: {model_prefix}: {str(e)}")
            return

        # For VFS storage, check if parent model directory is now empty and remove it
        if isinstance(storage, VFSStorage):
            await self._cleanup_empty_parent_directory(storage, model_id)

    async def _cleanup_empty_parent_directory(
        self,
        storage: VFSStorage,
        model_id: str,
    ) -> None:
        """Remove model directory and its empty parent directories recursively"""
        # Clean up model_id directory and all empty parent directories
        path_parts = model_id.split("/")

        # Start from the deepest directory and work up
        for i in range(len(path_parts), 0, -1):
            current_path = "/".join(path_parts[:i])
            if not current_path:
                continue

            try:
                entries = await storage.list_directory(current_path)
                if len(entries) == 0:
                    await storage.delete_file(current_path)
                    log.info(f"[cleanup] Removed empty directory: {current_path}")
                else:
                    # Directory not empty, stop climbing up
                    break
            except Exception as e:
                # Directory not found or other error - check if it's a "not found" type error
                error_str = str(e).lower()
                if "not found" in error_str or "does not exist" in error_str:
                    # Directory already removed or never existed - continue to parent
                    continue
                # Other error - log warning but continue to try parent directories
                log.warning(f"[cleanup] Failed to cleanup directory {current_path}: {str(e)}")
                break


class ImportPipeline:
    """Pipeline that executes import steps in sequence"""

    def __init__(self, steps: list[ImportStep[Any]]) -> None:
        self._steps = steps

    async def _cleanup_empty_parent_directory_if_vfs(
        self,
        step: ImportStep[Any],
        context: ImportStepContext,
    ) -> None:
        """Cleanup empty parent directory for VFS storage even when full cleanup is skipped"""
        from ai.backend.storage.storages.vfs_storage import VFSStorage

        try:
            storage = step.stage_storage(context)
            if isinstance(storage, VFSStorage):
                await step._cleanup_empty_parent_directory(storage, context.model.model_id)
        except Exception:
            # Ignore errors during empty directory cleanup
            pass

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
                        # Still cleanup empty parent directories that may remain after archive
                        await self._cleanup_empty_parent_directory_if_vfs(step, context)
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
