from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import cast, override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import ModelVerifyingEvent
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.context_types import ArtifactVerifierContext
from ai.backend.storage.exception import (
    ArtifactVerificationFailedError,
    ArtifactVerifyStorageTypeInvalid,
    NotImplementedAPI,
    StorageStepRequiredStepNotProvided,
)
from ai.backend.storage.services.artifacts.storage_transfer import StorageTransferManager
from ai.backend.storage.services.artifacts.types import (
    DownloadStepResult,
    ImportStep,
    ImportStepContext,
    VerifyStepResult,
)
from ai.backend.storage.storages.vfs_storage import VFSStorage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelVerifyStep(ImportStep[DownloadStepResult], ABC):
    """Base class for model verification steps that transfer files and run artifact verification"""

    _artifact_verifier_ctx: ArtifactVerifierContext
    _transfer_manager: StorageTransferManager
    _event_producer: EventProducer

    def __init__(
        self,
        artifact_verifier_ctx: ArtifactVerifierContext,
        transfer_manager: StorageTransferManager,
        event_producer: EventProducer,
    ) -> None:
        self._artifact_verifier_ctx = artifact_verifier_ctx
        self._transfer_manager = transfer_manager
        self._event_producer = event_producer

    @property
    def step_type(self) -> ArtifactStorageImportStep:
        return ArtifactStorageImportStep.VERIFY

    @property
    @abstractmethod
    def registry_type(self) -> ArtifactRegistryType:
        """Registry type used for revision resolution"""
        raise NotImplementedAPI

    @override
    async def execute(
        self, context: ImportStepContext, input_data: DownloadStepResult
    ) -> VerifyStepResult:
        source_storage_name = context.storage_step_mappings.get(ArtifactStorageImportStep.DOWNLOAD)
        dst_storage_name = context.storage_step_mappings.get(ArtifactStorageImportStep.VERIFY)
        if source_storage_name is None:
            raise StorageStepRequiredStepNotProvided(
                "No storage mapping provided for DOWNLOAD step"
            )
        if dst_storage_name is None:
            raise StorageStepRequiredStepNotProvided("No storage mapping provided for VERIFY step")

        revision = context.model.resolve_revision(self.registry_type)
        model_prefix = f"{context.model.model_id}/{revision}"

        # Send model verifying event
        await self._event_producer.anycast_event(
            ModelVerifyingEvent(
                model_id=context.model.model_id,
                revision=revision,
                registry_type=self.registry_type,
                registry_name=context.registry_name,
            )
        )

        await self._transfer_manager.transfer_directory(
            source_storage_name=source_storage_name,
            dest_storage_name=dst_storage_name,
            source_prefix=model_prefix,
            dest_prefix=model_prefix,
        )

        dst_storage = context.storage_pool.get_storage(dst_storage_name)
        if not isinstance(dst_storage, VFSStorage):
            raise ArtifactVerifyStorageTypeInvalid("Verify step requires VFS storage type")
        dst_storage = cast(VFSStorage, dst_storage)

        for verifier_name, verifier in self._artifact_verifier_ctx._verifiers.items():
            dst_path = dst_storage.resolve_path(model_prefix)
            log.info(
                f"Starting artifact verification using '{verifier_name}', dst_path: {dst_path}"
            )
            result = await verifier.verify(dst_path, context)
            if result.infected_count > 0:
                raise ArtifactVerificationFailedError(
                    f"Artifact '{model_prefix}' verification failed using '{verifier_name}': "
                    f"infected_count={result.infected_count}"
                )

            log.info(f"Artifact verification using '{verifier_name}' completed successfully")

        return VerifyStepResult(
            verified_files=input_data.downloaded_files,
            storage_name=dst_storage_name,
            total_bytes=input_data.total_bytes,
        )

    @override
    async def cleanup_stage(self, context: ImportStepContext) -> None:
        """Clean up files from verify storage on failure"""
        verify_storage = context.storage_step_mappings.get(ArtifactStorageImportStep.VERIFY)
        if not verify_storage:
            return

        # Delete entire model (cleaning up individual files is complex)
        revision = context.model.resolve_revision(self.registry_type)
        model_prefix = f"{context.model.model_id}/{revision}"

        try:
            storage = context.storage_pool.get_storage(verify_storage)
            await storage.delete_file(model_prefix)
            log.info(f"[cleanup] Removed verify files: {verify_storage}:{model_prefix}")
        except Exception as e:
            log.warning(
                f"[cleanup] Failed to cleanup verify: {verify_storage}:{model_prefix}: {str(e)}"
            )


class ModelArchiveStep(ImportStep[VerifyStepResult], ABC):
    """Base class for model archiving steps that transfer files to archive storage"""

    def __init__(self, transfer_manager: StorageTransferManager) -> None:
        self._transfer_manager = transfer_manager

    @property
    def step_type(self) -> ArtifactStorageImportStep:
        return ArtifactStorageImportStep.ARCHIVE

    @property
    @abstractmethod
    def registry_type(self) -> ArtifactRegistryType:
        """Registry type used for revision resolution"""
        raise NotImplementedAPI

    @override
    async def execute(
        self,
        context: ImportStepContext,
        input_data: VerifyStepResult,
    ) -> None:
        download_storage = input_data.storage_name
        archive_storage = context.storage_step_mappings.get(ArtifactStorageImportStep.ARCHIVE)

        if not archive_storage:
            raise StorageStepRequiredStepNotProvided("No storage mapping provided for ARCHIVE step")

        # No need to move if download and archive storage are the same
        if download_storage == archive_storage:
            log.info(
                f"Archive step skipped - download and archive storage are the same: {archive_storage}"
            )
            return

        log.info(f"Starting archive transfer: {download_storage} -> {archive_storage}")

        archieved_file_cnt = 0
        # Move each file from download storage to archive storage
        for file_info, storage_key in input_data.verified_files:
            try:
                archieved_file_cnt += await self._transfer_manager.transfer_directory(
                    source_storage_name=download_storage,
                    dest_storage_name=archive_storage,
                    source_prefix=storage_key,
                    dest_prefix=storage_key,
                )
                log.debug(f"Transferred file to archive: {storage_key}")
            except Exception as e:
                log.error(f"Failed to transfer file to archive: {storage_key}: {str(e)}")
                raise

        log.info(
            f"Archive transfer completed: {download_storage} -> {archive_storage}, "
            f"files={archieved_file_cnt}"
        )

    @override
    async def cleanup_stage(self, context: ImportStepContext) -> None:
        """Clean up files from archive storage on failure"""
        archive_storage = context.storage_step_mappings.get(ArtifactStorageImportStep.ARCHIVE)
        if not archive_storage:
            return

        # Delete entire model (cleaning up individual files is complex)
        revision = context.model.resolve_revision(self.registry_type)
        model_prefix = f"{context.model.model_id}/{revision}"

        try:
            storage = context.storage_pool.get_storage(archive_storage)
            await storage.delete_file(model_prefix)
            log.info(f"[cleanup] Removed archive files: {archive_storage}:{model_prefix}")
        except Exception as e:
            log.warning(
                f"[cleanup] Failed to cleanup archive: {archive_storage}:{model_prefix}: {str(e)}"
            )
