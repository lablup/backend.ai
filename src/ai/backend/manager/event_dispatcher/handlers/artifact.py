import logging
from uuid import UUID

from ai.backend.common.data.artifact.types import ArtifactRegistryType, VerificationStepResult
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.artifact.anycast import (
    ModelImportDoneEvent,
    ModelMetadataFetchDoneEvent,
    ModelVerifyingEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.artifact.types import ArtifactStatus
from ai.backend.manager.errors.artifact_registry import InvalidArtifactRegistryTypeError
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.huggingface_registry.repository import HuggingFaceRepository
from ai.backend.manager.repositories.reservoir_registry.repository import (
    ReservoirRegistryRepository,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ArtifactEventHandler:
    _artifact_repository: ArtifactRepository
    _huggingface_repository: HuggingFaceRepository
    _reservoir_repository: ReservoirRegistryRepository
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer

    def __init__(
        self,
        artifact_repository: ArtifactRepository,
        huggingface_repository: HuggingFaceRepository,
        reservoir_repository: ReservoirRegistryRepository,
        config_provider: ManagerConfigProvider,
        event_producer: EventProducer,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._huggingface_repository = huggingface_repository
        self._reservoir_repository = reservoir_repository
        self._config_provider = config_provider
        self._event_producer = event_producer

    async def handle_model_verifying(
        self,
        context: None,
        source: AgentId,
        event: ModelVerifyingEvent,
    ) -> None:
        try:
            registry_type = ArtifactRegistryType(event.registry_type)
        except Exception:
            raise InvalidArtifactRegistryTypeError(
                f"Unsupported artifact registry type: {event.registry_type}"
            )
        registry_id: UUID
        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                huggingface_registry_data = (
                    await self._huggingface_repository.get_registry_data_by_name(
                        event.registry_name
                    )
                )
                registry_id = huggingface_registry_data.id
            case ArtifactRegistryType.RESERVOIR:
                registry_data = await self._reservoir_repository.get_registry_data_by_name(
                    event.registry_name
                )
                registry_id = registry_data.id

        artifact = await self._artifact_repository.get_model_artifact(
            event.model_id, registry_id=registry_id
        )

        # Get the specific revision
        revision = await self._artifact_repository.get_artifact_revision(
            artifact.id, revision=event.revision
        )

        if revision.status == ArtifactStatus.PULLING:
            await self._artifact_repository.update_artifact_revision_status(
                revision.id, ArtifactStatus.VERIFYING
            )

    async def _produce_artifact_download_notification(
        self,
        artifact_id: UUID,
        artifact_name: str,
        artifact_type: str,
        registry_type: str,
        registry_id: UUID,
        version: str,
        status: ArtifactStatus,
        success: bool,
        digest: str | None,
        verification_result: VerificationStepResult | None,
    ) -> None:
        """Produce notification event for artifact download completion."""
        from datetime import datetime, timezone

        from ai.backend.common.data.notification import NotificationRuleType
        from ai.backend.common.data.notification.messages import ArtifactDownloadCompletedMessage
        from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent

        try:
            message = ArtifactDownloadCompletedMessage(
                artifact_id=str(artifact_id),
                artifact_name=artifact_name,
                artifact_type=artifact_type,
                registry_type=registry_type,
                registry_id=str(registry_id),
                version=version,
                status=status.value,
                success=success,
                digest=digest,
                verification_result=(
                    verification_result.model_dump() if verification_result else None
                ),
            )
            event = NotificationTriggeredEvent(
                rule_type=NotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED.value,
                timestamp=datetime.now(timezone.utc),
                notification_data=message.model_dump(),
            )
            await self._event_producer.anycast_event(event)
            log.debug(
                "Produced artifact download notification for artifact {} revision {}",
                artifact_id,
                version,
            )
        except Exception as e:
            log.error(
                "Failed to produce artifact download notification for artifact {} revision {}: {}",
                artifact_id,
                version,
                e,
            )

    async def handle_model_import_done(
        self,
        context: None,
        source: AgentId,
        event: ModelImportDoneEvent,
    ) -> None:
        try:
            registry_type = ArtifactRegistryType(event.registry_type)
        except Exception:
            raise InvalidArtifactRegistryTypeError(
                f"Unsupported artifact registry type: {event.registry_type}"
            )
        registry_id: UUID
        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                huggingface_registry_data = (
                    await self._huggingface_repository.get_registry_data_by_name(
                        event.registry_name
                    )
                )
                registry_id = huggingface_registry_data.id
            case ArtifactRegistryType.RESERVOIR:
                registry_data = await self._reservoir_repository.get_registry_data_by_name(
                    event.registry_name
                )
                registry_id = registry_data.id

        artifact = await self._artifact_repository.get_model_artifact(
            event.model_id, registry_id=registry_id
        )

        # Get the specific revision
        revision = await self._artifact_repository.get_artifact_revision(
            artifact.id, revision=event.revision
        )

        if event.success is False:
            log.warning("Model import failed: {} revision: {}", event.model_id, event.revision)
            await self._artifact_repository.update_artifact_revision_status(
                revision.id, ArtifactStatus.FAILED
            )
            # Produce notification for failed download
            await self._produce_artifact_download_notification(
                artifact_id=artifact.id,
                artifact_name=artifact.name,
                artifact_type=artifact.type.value,
                registry_type=artifact.registry_type.value,
                registry_id=registry_id,
                version=revision.version,
                status=ArtifactStatus.FAILED,
                success=False,
                digest=revision.digest,
                verification_result=event.verification_result,
            )
            return

        if event.digest:
            await self._artifact_repository.update_artifact_revision_digest(
                revision.id, event.digest
            )

        # Update verification_result if verification step was executed
        if event.verification_result:
            await self._artifact_repository.update_artifact_revision_verification_result(
                revision.id, event.verification_result
            )

        final_status: ArtifactStatus
        try:
            reservoir_config = self._config_provider.config.reservoir
            if reservoir_config is None:
                raise ServerMisconfiguredError("Reservoir configuration is missing.")
            if reservoir_config.enable_approve_process:
                final_status = ArtifactStatus.NEEDS_APPROVAL
                await self._artifact_repository.update_artifact_revision_status(
                    revision.id, final_status
                )
            else:
                final_status = ArtifactStatus.AVAILABLE
                await self._artifact_repository.update_artifact_revision_status(
                    revision.id, final_status
                )
        except Exception as model_error:
            log.error(
                "Failed to process imported model update: {} - {}",
                event.model_id,
                model_error,
            )
            final_status = ArtifactStatus.FAILED

        # Produce notification for successful download
        await self._produce_artifact_download_notification(
            artifact_id=artifact.id,
            artifact_name=artifact.name,
            artifact_type=artifact.type.value,
            registry_type=artifact.registry_type.value,
            registry_id=registry_id,
            version=revision.version,
            status=final_status,
            success=True,
            digest=event.digest or revision.digest,
            verification_result=event.verification_result,
        )

    async def handle_model_metadata_fetch_done(
        self,
        context: None,
        source: AgentId,
        event: ModelMetadataFetchDoneEvent,
    ) -> None:
        model_info = event.model
        try:
            registry_type = ArtifactRegistryType(model_info.registry_type)
        except Exception:
            raise InvalidArtifactRegistryTypeError(
                f"Unsupported artifact registry type: {model_info.registry_type}"
            )

        registry_id: UUID
        match registry_type:
            case ArtifactRegistryType.HUGGINGFACE:
                huggingface_registry_data = (
                    await self._huggingface_repository.get_registry_data_by_name(
                        model_info.registry_name
                    )
                )
                registry_id = huggingface_registry_data.id
            case ArtifactRegistryType.RESERVOIR:
                registry_data = await self._reservoir_repository.get_registry_data_by_name(
                    model_info.registry_name
                )
                registry_id = registry_data.id

        artifact = await self._artifact_repository.get_model_artifact(
            model_info.model_id, registry_id=registry_id
        )

        # Get the specific revision
        revision = await self._artifact_repository.get_artifact_revision(
            artifact.id, revision=model_info.revision
        )

        try:
            # Update the README content
            await self._artifact_repository.update_artifact_revision_readme(
                revision.id, model_info.readme_content
            )

            # Update the file size
            await self._artifact_repository.update_artifact_revision_bytesize(
                revision.id, model_info.size
            )

            log.trace(
                "Updated metadata for model: {} revision: {} in artifact: {} (size: {} bytes)",
                model_info.model_id,
                model_info.revision,
                artifact.id,
                model_info.size,
            )
        except Exception as model_error:
            log.error(
                "Failed to process metadata update for model: {} - {}",
                model_info.model_id,
                model_error,
            )
