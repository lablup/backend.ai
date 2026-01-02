from collections.abc import Mapping
from typing import Optional
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import AgentId, ImageAlias, ImageID
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.image.types import (
    ImageAgentInstallStatus,
    ImageAliasData,
    ImageData,
    ImageDataWithDetails,
    ImageStatus,
    ImageWithAgentInstallStatus,
    RescanImagesResult,
)
from ai.backend.manager.models.image import (
    ImageIdentifier,
    ImageRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.image.db_source.db_source import ImageDBSource
from ai.backend.manager.repositories.image.stateful_source.stateful_source import (
    ImageStatefulSource,
)

image_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.IMAGE_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class ImageRepository:
    _db_source: ImageDBSource
    _stateful_source: ImageStatefulSource
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_image: ValkeyImageClient,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = ImageDBSource(db)
        self._stateful_source = ImageStatefulSource(valkey_image)
        self._config_provider = config_provider

    @image_repository_resilience.apply()
    async def resolve_image(
        self, identifiers: list[ImageAlias | ImageRef | ImageIdentifier]
    ) -> ImageData:
        """
        Resolves an image by its identifiers, which can be a combination of
        ImageAlias, ImageRef, or ImageIdentifier.
        Returns an ImageData object.
        Raises Exception if the image cannot be resolved.
        """
        return await self._db_source.fetch_image_by_identifiers(identifiers)

    @image_repository_resilience.apply()
    async def resolve_images_batch(
        self, identifier_lists: list[list[ImageIdentifier]]
    ) -> list[ImageData]:
        """
        Resolves multiple images by their identifiers in a single database session.
        Returns a list of ImageData objects.
        More efficient than multiple individual resolve_image calls.
        """
        return await self._db_source.fetch_images_batch(identifier_lists)

    @image_repository_resilience.apply()
    async def get_images_by_canonicals(
        self,
        image_canonicals: list[str],
        status_filter: Optional[list[ImageStatus]] = None,
        requested_by_superadmin: bool = False,
    ) -> list[ImageWithAgentInstallStatus]:
        images_data = await self._db_source.query_images_by_canonicals(
            image_canonicals, status_filter
        )
        image_ids = list(images_data.keys())
        installed_agents_for_images = await self._stateful_source.list_agents_with_images(image_ids)

        hide_agents = (
            False if requested_by_superadmin else self._config_provider.config.manager.hide_agents
        )

        images_with_agent_install_status: list[ImageWithAgentInstallStatus] = []
        for image_id, image in images_data.items():
            installed_agents = installed_agents_for_images.get(image_id, set())
            images_with_agent_install_status.append(
                ImageWithAgentInstallStatus(
                    image=image,
                    agent_install_status=ImageAgentInstallStatus(
                        installed=bool(installed_agents),
                        agent_names=[] if hide_agents else list(installed_agents),
                    ),
                )
            )

        return images_with_agent_install_status

    @image_repository_resilience.apply()
    async def get_image_by_identifier(
        self,
        identifier: ImageIdentifier,
        status_filter: Optional[list[ImageStatus]] = None,
        requested_by_superadmin: bool = False,
    ) -> ImageWithAgentInstallStatus:
        image_data: ImageDataWithDetails = await self._db_source.query_image_details_by_identifier(
            identifier, status_filter
        )
        installed_agents = await self._stateful_source.list_agents_with_image(image_data.id)
        hide_agents = (
            False if requested_by_superadmin else self._config_provider.config.manager.hide_agents
        )

        return ImageWithAgentInstallStatus(
            image=image_data,
            agent_install_status=ImageAgentInstallStatus(
                installed=bool(installed_agents),
                agent_names=[] if hide_agents else list(installed_agents),
            ),
        )

    @image_repository_resilience.apply()
    async def get_image_by_id(
        self,
        image_id: UUID,
        load_aliases: bool = False,
        status_filter: Optional[list[ImageStatus]] = None,
        requested_by_superadmin: bool = False,
    ) -> ImageWithAgentInstallStatus:
        image_data: ImageDataWithDetails = await self._db_source.query_image_details_by_id(
            image_id, load_aliases, status_filter
        )
        installed_agents = await self._stateful_source.list_agents_with_image(image_data.id)
        hide_agents = (
            False if requested_by_superadmin else self._config_provider.config.manager.hide_agents
        )

        return ImageWithAgentInstallStatus(
            image=image_data,
            agent_install_status=ImageAgentInstallStatus(
                installed=bool(installed_agents),
                agent_names=[] if hide_agents else list(installed_agents),
            ),
        )

    @image_repository_resilience.apply()
    async def get_image_installed_agents(
        self, image_ids: list[ImageID]
    ) -> Mapping[ImageID, set[AgentId]]:
        """
        Returns the set of installed agents for each image ID in the input list.
        The result is a dictionary mapping ImageID to the set of installed agents.
        """
        return await self._stateful_source.list_agents_with_images(image_ids)

    @image_repository_resilience.apply()
    async def get_all_images(
        self, status_filter: Optional[list[ImageStatus]] = None
    ) -> Mapping[ImageID, ImageWithAgentInstallStatus]:
        """
        Retrieves all images from the database, optionally filtered by status.
        Returns a mapping of ImageID to ImageWithAgentInstallStatus.
        """
        image_data = await self._db_source.query_all_images(status_filter)
        installed_agents = await self._stateful_source.list_agents_with_images(
            list(image_data.keys())
        )
        return {
            image_id: ImageWithAgentInstallStatus(
                image=image_info,
                agent_install_status=ImageAgentInstallStatus(
                    installed=bool(installed_agents.get(image_id, set())),
                    agent_names=list(installed_agents.get(image_id, set())),
                ),
            )
            for image_id, image_info in image_data.items()
        }

    @image_repository_resilience.apply()
    async def soft_delete_user_image(
        self,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
        user_id: UUID,
    ) -> ImageData:
        """
        Marks an image as deleted for a specific user.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        return await self._db_source.mark_user_image_deleted(identifiers, user_id)

    @image_repository_resilience.apply()
    async def soft_delete_image_by_id(
        self,
        image_id: UUID,
        user_id: UUID,
    ) -> ImageData:
        """
        Marks an image as deleted by its ID.
        Validates ownership by user_id before deletion.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        return await self._db_source.mark_image_deleted_by_id(image_id, user_id)

    @image_repository_resilience.apply()
    async def get_and_validate_image_ownership(
        self, image_id: UUID, user_id: UUID, load_aliases: bool = False
    ) -> ImageData:
        """
        Gets an image by ID and validates ownership in a single operation.
        Raises ForgetImageActionGenericForbiddenError if image doesn't exist or user doesn't own it.
        """
        return await self._db_source.validate_and_fetch_image_ownership(
            image_id, user_id, load_aliases
        )

    @image_repository_resilience.apply()
    async def add_image_alias(
        self, alias: str, image_canonical: str, architecture: str
    ) -> tuple[UUID, ImageAliasData]:
        return await self._db_source.insert_image_alias(alias, image_canonical, architecture)

    @image_repository_resilience.apply()
    async def get_image_alias(self, alias: str) -> ImageAliasData:
        return await self._db_source.query_image_alias(alias)

    @image_repository_resilience.apply()
    async def delete_image_alias(self, alias: str) -> tuple[UUID, ImageAliasData]:
        return await self._db_source.remove_image_alias(alias)

    @image_repository_resilience.apply()
    async def scan_image_by_identifier(
        self, image_canonical: str, architecture: str
    ) -> RescanImagesResult:
        """
        Scans a single image by resolving it first and then scanning.
        Returns RescanImagesResult with the scanned image data.
        """
        return await self._db_source.scan_and_upsert_image(image_canonical, architecture)

    @image_repository_resilience.apply()
    async def untag_image_from_registry(self, image_id: UUID) -> Optional[ImageData]:
        return await self._db_source.remove_tag_from_registry(image_id)

    @image_repository_resilience.apply()
    async def update_image_properties(self, updater: Updater[ImageRow]) -> ImageData:
        return await self._db_source.modify_image_properties(updater)

    @image_repository_resilience.apply()
    async def clear_image_custom_resource_limit(
        self, image_canonical: str, architecture: str
    ) -> ImageData:
        return await self._db_source.clear_image_resource_limits(image_canonical, architecture)

    @image_repository_resilience.apply()
    async def untag_image_from_registry_validated(self, image_id: UUID, user_id: UUID) -> ImageData:
        """
        Validates ownership and untags an image from registry in a single operation.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """
        return await self._db_source.remove_tag_from_registry_with_validation(image_id, user_id)

    @image_repository_resilience.apply()
    async def delete_image_with_aliases_validated(self, image_id: UUID, user_id: UUID) -> ImageData:
        """
        Deletes an image and all its aliases after validating ownership.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """
        return await self._db_source.remove_image_and_aliases_with_validation(image_id, user_id)
