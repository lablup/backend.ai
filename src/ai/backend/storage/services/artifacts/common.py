from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import cast, override

from ai.backend.common.artifact_storage import AbstractStorage
from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    VerificationStepResult,
    VerifierResult,
)
from ai.backend.common.data.storage.types import ArtifactStorageImportStep
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import (
    ModelVerifyingEvent,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.context_types import ArtifactVerifierContext
from ai.backend.storage.data.storage.types import StorageTarget
from ai.backend.storage.errors import (
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
from ai.backend.storage.storages.vfolder_storage import VFolderStorage
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
    def stage_storage(self, context: ImportStepContext) -> AbstractStorage:
        verify_storage_target: StorageTarget | None = context.storage_step_mappings.get(
            ArtifactStorageImportStep.VERIFY
        )
        if not verify_storage_target:
            raise StorageStepRequiredStepNotProvided(
                "No storage mapping provided for VERIFY step cleanup"
            )

        return verify_storage_target.resolve_storage(context.storage_pool)

    @override
    async def execute(
        self, context: ImportStepContext, input_data: DownloadStepResult
    ) -> VerifyStepResult:
        source_storage_target: StorageTarget | None = context.storage_step_mappings.get(
            ArtifactStorageImportStep.DOWNLOAD
        )
        dst_storage_target: StorageTarget | None = context.storage_step_mappings.get(
            ArtifactStorageImportStep.VERIFY
        )
        if source_storage_target is None:
            raise StorageStepRequiredStepNotProvided(
                "No storage mapping provided for DOWNLOAD step"
            )
        if dst_storage_target is None:
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
            source_storage=source_storage_target,
            dest_storage=dst_storage_target,
            source_prefix=model_prefix,
            dest_prefix=model_prefix,
        )

        dst_storage = dst_storage_target.resolve_storage(context.storage_pool)
        if not isinstance(dst_storage, (VFSStorage, VFolderStorage)):
            raise ArtifactVerifyStorageTypeInvalid(
                "Verify step requires VFS or VFolderStorage storage type"
            )
        dst_storage = cast(VFSStorage | VFolderStorage, dst_storage)

        # Collect verification results from all verifiers
        verifier_results: dict[str, VerifierResult] = {}
        verification_success = True

        for verifier_name, verifier in self._artifact_verifier_ctx._verifiers.items():
            dst_path = dst_storage.resolve_path(model_prefix)
            verifier_start_time = datetime.now(UTC)
            log.info(
                f"Starting artifact verification using '{verifier_name}', dst_path: {dst_path}"
            )
            try:
                result = await verifier.verify(dst_path, context)
                verifier_end_time = datetime.now(UTC)
                elapsed_time = (verifier_end_time - verifier_start_time).total_seconds()

                # Create VerifierResult object
                verifier_results[verifier_name] = VerifierResult(
                    success=result.infected_count == 0,
                    infected_count=result.infected_count,
                    scanned_at=verifier_start_time,
                    scan_time=elapsed_time,
                    scanned_count=result.scanned_count,
                    metadata=result.metadata,
                )

                if result.infected_count > 0:
                    verification_success = False
                    log.warning(
                        f"Artifact verification using '{verifier_name}' found {result.infected_count} infected files"
                    )
                else:
                    log.info(
                        f"Artifact verification using '{verifier_name}' completed successfully"
                    )

            except Exception as e:
                verification_success = False
                verifier_end_time = datetime.now(UTC)
                elapsed_time = (verifier_end_time - verifier_start_time).total_seconds()
                verifier_results[verifier_name] = VerifierResult(
                    success=False,
                    infected_count=0,
                    scanned_at=verifier_start_time,
                    scan_time=elapsed_time,
                    scanned_count=0,
                    metadata={},
                    error=str(e),
                )
                log.error(f"Artifact verification using '{verifier_name}' failed: {e}")

        # Create complete verification result
        verification_result = VerificationStepResult(
            verifiers=verifier_results,
        )

        # Store verification result in context for later use
        context.step_metadata["verification_result"] = verification_result

        # Raise error if any verification failed
        if not verification_success:
            raise ArtifactVerificationFailedError(
                f"Artifact '{model_prefix}' verification failed. See verification_result for details."
            )

        return VerifyStepResult(
            verified_files=input_data.downloaded_files,
            storage_name=dst_storage_target.name,
            total_bytes=input_data.total_bytes,
            verification_result=verification_result,
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
    def stage_storage(self, context: ImportStepContext) -> AbstractStorage:
        archive_storage_target: StorageTarget | None = context.storage_step_mappings.get(
            ArtifactStorageImportStep.ARCHIVE
        )
        if not archive_storage_target:
            raise StorageStepRequiredStepNotProvided(
                "No storage mapping provided for ARCHIVE step cleanup"
            )

        return archive_storage_target.resolve_storage(context.storage_pool)

    @override
    async def execute(
        self,
        context: ImportStepContext,
        input_data: VerifyStepResult,
    ) -> None:
        download_storage_name = input_data.storage_name
        archive_storage_target: StorageTarget | None = context.storage_step_mappings.get(
            ArtifactStorageImportStep.ARCHIVE
        )

        if not archive_storage_target:
            raise StorageStepRequiredStepNotProvided("No storage mapping provided for ARCHIVE step")

        archive_storage_name = archive_storage_target.name

        # No need to move if download and archive storage are the same
        if download_storage_name == archive_storage_name:
            log.info(
                "Archive step skipped - download and archive storage are the same: {}",
                archive_storage_name,
            )
            return

        log.info("Starting archive transfer: {} -> {}", download_storage_name, archive_storage_name)

        # Transfer entire model directory at once
        revision = context.model.resolve_revision(self.registry_type)
        model_prefix = f"{context.model.model_id}/{revision}"

        # Get source storage from VERIFY step mapping (where files are after verification)
        verify_storage_target: StorageTarget | None = context.storage_step_mappings.get(
            ArtifactStorageImportStep.VERIFY
        )
        if not verify_storage_target:
            raise StorageStepRequiredStepNotProvided("No storage mapping provided for VERIFY step")

        archived_file_cnt = await self._transfer_manager.transfer_directory(
            source_storage=verify_storage_target,
            dest_storage=archive_storage_target,
            source_prefix=model_prefix,
            dest_prefix=model_prefix,
        )

        log.info(
            "Archive transfer completed: {} -> {}, files={}",
            download_storage_name,
            archive_storage_name,
            archived_file_cnt,
        )
