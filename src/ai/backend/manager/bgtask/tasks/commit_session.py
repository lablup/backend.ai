from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Optional, cast, override

from pydantic import Field

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
    BaseBackgroundTaskResult,
)
from ai.backend.common.data.session.types import CustomizedImageVisibilityScope
from ai.backend.common.docker import DEFAULT_KERNEL_FEATURE, KernelFeatures, LabelName
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BaseBgtaskDoneEvent,
    BaseBgtaskEvent,
    BgtaskStatus,
)
from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.common.events.types import EventCacheDomain, EventDomain
from ai.backend.common.exception import BgtaskCancelledError, BgtaskFailedError
from ai.backend.common.types import ImageRegistry, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.bgtask.types import ManagerBgtaskName
from ai.backend.manager.data.image.types import ImageIdentifier

if TYPE_CHECKING:
    from ai.backend.common.events.fetcher import EventFetcher
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.manager.models.image import ImageRow
    from ai.backend.manager.registry import AgentRegistry
    from ai.backend.manager.repositories.session.repository import SessionRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class CommitSessionResult(BaseBackgroundTaskResult):
    """
    Result of commit session background task.
    Contains the rescanned image ID or error message.
    """

    image_id: Optional[uuid.UUID] = Field(
        default=None, description="ID of the rescanned image after commit"
    )
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")


class CommitSessionManifest(BaseBackgroundTaskManifest):
    """
    Manifest for committing a session and uploading it as a customized image.
    """

    session_id: SessionId = Field(description="Session ID to commit")
    registry_hostname: str = Field(description="Registry hostname to push the image")
    registry_project: str = Field(description="Registry project name")
    image_name: str = Field(description="Name for the customized image")
    image_visibility: CustomizedImageVisibilityScope = Field(
        description="Visibility scope of the customized image"
    )
    image_owner_id: str = Field(description="Owner ID of the customized image")
    user_email: str = Field(description="User email for customized image metadata")


class CommitSessionHandler(BaseBackgroundTaskHandler[CommitSessionManifest, CommitSessionResult]):
    """
    Background task handler for committing sessions and uploading as customized images.
    """

    _session_repository: SessionRepository
    _agent_registry: AgentRegistry
    _event_hub: EventHub
    _event_fetcher: EventFetcher

    def __init__(
        self,
        session_repository: SessionRepository,
        agent_registry: AgentRegistry,
        event_hub: EventHub,
        event_fetcher: EventFetcher,
    ) -> None:
        self._session_repository = session_repository
        self._agent_registry = agent_registry
        self._event_hub = event_hub
        self._event_fetcher = event_fetcher

    @classmethod
    @override
    def name(cls) -> ManagerBgtaskName:
        return ManagerBgtaskName.COMMIT_SESSION  # type: ignore[return-value]

    @classmethod
    @override
    def manifest_type(cls) -> type[CommitSessionManifest]:
        return CommitSessionManifest

    @override
    async def execute(self, manifest: CommitSessionManifest) -> CommitSessionResult:
        try:
            # Get session and validate
            session = await self._session_repository.get_session_by_id(manifest.session_id)
            if not session:
                error_msg = f"Session {manifest.session_id} not found"
                log.error(error_msg)
                return CommitSessionResult(error_message=error_msg)

            # Get registry configuration
            registry_conf = await self._session_repository.get_container_registry(
                manifest.registry_hostname, manifest.registry_project
            )
            if not registry_conf:
                error_msg = f"Project {manifest.registry_project} not found in registry {manifest.registry_hostname}"
                log.error(error_msg)
                return CommitSessionResult(error_message=error_msg)

            # Resolve base image
            image_row = await self._session_repository.resolve_image([
                ImageIdentifier(session.main_kernel.image, session.main_kernel.architecture)
            ])
            base_image_ref = image_row.image_ref

            # Build new image canonical name
            filtered_tag_set = [
                x for x in base_image_ref.tag.split("-") if not x.startswith("customized_")
            ]

            if base_image_ref.name == "":
                new_name = base_image_ref.project
            else:
                new_name = base_image_ref.name

            new_canonical = f"{manifest.registry_hostname}/{manifest.registry_project}/{new_name}:{'-'.join(filtered_tag_set)}"

            # Check for existing customized image
            existing_row = await self._session_repository.get_existing_customized_image(
                new_canonical,
                manifest.image_visibility.value,
                manifest.image_owner_id,
                manifest.image_name,
            )

            customized_image_id: str
            kern_features: list[str]
            if existing_row is not None:
                existing_image: ImageRow = existing_row
                labels = existing_image.labels or {}
                kern_features_str = labels.get(LabelName.FEATURES, DEFAULT_KERNEL_FEATURE)
                kern_features = (
                    kern_features_str.split() if kern_features_str else [DEFAULT_KERNEL_FEATURE]
                )
                customized_image_id = labels.get(LabelName.CUSTOMIZED_ID, str(uuid.uuid4()))
                log.debug("reusing existing customized image ID {}", customized_image_id)
            else:
                kern_features = [DEFAULT_KERNEL_FEATURE]
                customized_image_id = str(uuid.uuid4())
                # Remove PRIVATE label for customized images
                kern_features = [
                    feat for feat in kern_features if feat != KernelFeatures.PRIVATE.value
                ]

            new_canonical += f"-customized_{customized_image_id.replace('-', '')}"

            from ai.backend.common.docker import ImageRef

            new_image_ref = ImageRef.from_image_str(
                new_canonical,
                None,
                manifest.registry_hostname,
                architecture=base_image_ref.architecture,
                is_local=base_image_ref.is_local,
            )

            # Prepare image labels
            image_labels: dict[str | LabelName, str] = {
                LabelName.CUSTOMIZED_OWNER: f"{manifest.image_visibility.value}:{manifest.image_owner_id}",
                LabelName.CUSTOMIZED_NAME: manifest.image_name,
                LabelName.CUSTOMIZED_ID: customized_image_id,
                LabelName.FEATURES: " ".join(kern_features),
            }
            match manifest.image_visibility:
                case CustomizedImageVisibilityScope.USER:
                    image_labels[LabelName.CUSTOMIZED_USER_EMAIL] = manifest.user_email

            # Commit session
            log.info("Committing session {}", manifest.session_id)
            resp = await self._agent_registry.commit_session(
                session,
                new_image_ref,
                extra_labels=image_labels,
            )
            bgtask_id = cast(uuid.UUID, resp["bgtask_id"])

            # Wait for commit to complete
            await self._wait_for_agent_bgtask(bgtask_id, "Commit")

            # Push image to registry if not local
            if not new_image_ref.is_local:
                log.info("Pushing image to registry")
                image_registry = ImageRegistry(
                    name=manifest.registry_hostname,
                    url=str(registry_conf.url),
                    username=registry_conf.username,
                    password=registry_conf.password,
                )
                resp = await self._agent_registry.push_image(
                    session.main_kernel.agent,
                    new_image_ref,
                    image_registry,
                )
                bgtask_id = cast(uuid.UUID, resp["bgtask_id"])
                await self._wait_for_agent_bgtask(bgtask_id, "Push")

            # Rescan updated image
            log.info("Rescanning image")
            rescan_result = await self._session_repository.rescan_images(
                new_image_ref.canonical,
                manifest.registry_project,
                reporter=None,
            )

            if len(rescan_result.images) == 0:
                rescan_errors = ",".join(rescan_result.errors)
                error_msg = (
                    f"Session commit succeeded, but no image was rescanned, Error: {rescan_errors}"
                )
                log.error(error_msg)
                return CommitSessionResult(error_message=error_msg)
            elif len(rescan_result.images) > 1:
                log.warning(
                    "More than two images were rescanned unexpectedly. Rescanned Images: {}",
                    rescan_result.images,
                )

            result_image_id = rescan_result.images[0].id
            log.info("Session commit completed successfully. Image ID: {}", result_image_id)
            return CommitSessionResult(image_id=result_image_id)

        except Exception as e:
            log.exception("Failed to commit session {}", manifest.session_id)
            return CommitSessionResult(error_message=str(e))

    async def _wait_for_agent_bgtask(self, bgtask_id: uuid.UUID, operation_name: str) -> None:
        """Wait for an agent background task to complete."""
        propagator = WithCachePropagator(self._event_fetcher)
        self._event_hub.register_event_propagator(
            propagator, [(EventDomain.BGTASK, str(bgtask_id))]
        )
        try:
            cache_id = EventCacheDomain.BGTASK.cache_id(str(bgtask_id))
            async for event in propagator.receive(cache_id):
                if not isinstance(event, BaseBgtaskEvent):
                    log.warning("unexpected event: {}", event)
                    continue
                match event.status():
                    case BgtaskStatus.DONE | BgtaskStatus.PARTIAL_SUCCESS:
                        log.info("{} completed", operation_name)
                        return
                    case BgtaskStatus.FAILED:
                        error_msg = cast(BaseBgtaskDoneEvent, event).message
                        log.error("{} failed: {}", operation_name, error_msg)
                        raise BgtaskFailedError(extra_msg=error_msg)
                    case BgtaskStatus.CANCELLED:
                        log.warning("{} cancelled", operation_name)
                        raise BgtaskCancelledError(extra_msg="Operation cancelled")
                    case BgtaskStatus.UPDATED:
                        continue
                    case _:
                        log.warning("unexpected bgtask done event: {}", event)
        finally:
            self._event_hub.unregister_event_propagator(propagator.id())
