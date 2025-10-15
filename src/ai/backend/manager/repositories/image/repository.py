from typing import Optional
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import ImageAlias
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
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
        return await self._db_source.resolve_image(identifiers)

    @image_repository_resilience.apply()
    async def resolve_images_batch(
        self, identifier_lists: list[list[ImageIdentifier]]
    ) -> list[ImageData]:
        """
        Resolves multiple images by their identifiers in a single database session.
        Returns a list of ImageData objects.
        More efficient than multiple individual resolve_image calls.
        """
        return await self._db_source.resolve_images_batch(identifier_lists)

    @image_repository_resilience.apply()
    async def get_images_by_canonicals(
        self,
        image_canonicals: list[str],
        status_filter: Optional[list[ImageStatus]] = None,
        requested_by_superadmin: bool = False,
    ) -> list[ImageWithAgentInstallStatus]:
        images_data: list[ImageDataWithDetails] = await self._db_source.get_images_by_canonicals(
            image_canonicals, status_filter
        )

        installed_agents_for_images: list[set[str]] = []

        image_names = [image.name for image in images_data]
        installed_agents_for_images = await self._stateful_source.get_agents_for_images(image_names)

        # TODO: Handle mismatch in lengths more gracefully
        if len(installed_agents_for_images) != len(images_data):
            installed_agents_for_images = [set() for _ in images_data]

        hide_agents = (
            False if requested_by_superadmin else self._config_provider.config.manager.hide_agents
        )

        images_with_agent_install_status: list[ImageWithAgentInstallStatus] = []
        for image, installed_agents in zip(images_data, installed_agents_for_images):
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
        image_data: ImageDataWithDetails = await self._db_source.get_image_details_by_identifier(
            identifier, status_filter
        )
        installed_agents = await self._stateful_source.get_agents_for_image(image_data.name)
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
        image_data: ImageDataWithDetails = await self._db_source.get_image_details_by_id(
            image_id, load_aliases, status_filter
        )
        installed_agents = await self._stateful_source.get_agents_for_image(image_data.name)
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
    async def soft_delete_user_image(
        self,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
        user_id: UUID,
    ) -> ImageData:
        """
        Marks an image as deleted for a specific user.
        Raises ForgetImageActionGenericForbiddenError if the user does not own the image.
        """
        return await self._db_source.soft_delete_user_image(identifiers, user_id)

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
        return await self._db_source.soft_delete_image_by_id(image_id, user_id)

    @image_repository_resilience.apply()
    async def get_and_validate_image_ownership(
        self, image_id: UUID, user_id: UUID, load_aliases: bool = False
    ) -> ImageData:
        """
        Gets an image by ID and validates ownership in a single operation.
        Raises ForgetImageActionGenericForbiddenError if image doesn't exist or user doesn't own it.
        """
        return await self._db_source.get_and_validate_image_ownership(
            image_id, user_id, load_aliases
        )

    @image_repository_resilience.apply()
    async def add_image_alias(
        self, alias: str, image_canonical: str, architecture: str
    ) -> tuple[UUID, ImageAliasData]:
        return await self._db_source.add_image_alias(alias, image_canonical, architecture)

    @image_repository_resilience.apply()
    async def get_image_alias(self, alias: str) -> ImageAliasData:
        return await self._db_source.get_image_alias(alias)

    @image_repository_resilience.apply()
    async def delete_image_alias(self, alias: str) -> tuple[UUID, ImageAliasData]:
        return await self._db_source.delete_image_alias(alias)

    @image_repository_resilience.apply()
    async def scan_image_by_identifier(
        self, image_canonical: str, architecture: str
    ) -> RescanImagesResult:
        """
        Scans a single image by resolving it first and then scanning.
        Returns RescanImagesResult with the scanned image data.
        """
        return await self._db_source.scan_image_by_identifier(image_canonical, architecture)

    @image_repository_resilience.apply()
    async def untag_image_from_registry(self, image_id: UUID) -> Optional[ImageData]:
        return await self._db_source.untag_image_from_registry(image_id)

    @image_repository_resilience.apply()
    async def update_image_properties(
        self, target: str, architecture: str, properties_to_update: dict
    ) -> ImageData:
        return await self._db_source.update_image_properties(
            target, architecture, properties_to_update
        )

    @image_repository_resilience.apply()
    async def clear_image_custom_resource_limit(
        self, image_canonical: str, architecture: str
    ) -> ImageData:
        return await self._db_source.clear_image_custom_resource_limit(
            image_canonical, architecture
        )

    @image_repository_resilience.apply()
    async def untag_image_from_registry_validated(self, image_id: UUID, user_id: UUID) -> ImageData:
        """
        Validates ownership and untags an image from registry in a single operation.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """
        return await self._db_source.untag_image_from_registry_validated(image_id, user_id)

    @image_repository_resilience.apply()
    async def delete_image_with_aliases_validated(self, image_id: UUID, user_id: UUID) -> ImageData:
        """
        Deletes an image and all its aliases after validating ownership.
        Raises ForgetImageActionGenericForbiddenError if user doesn't own the image.
        """
        return await self._db_source.delete_image_with_aliases_validated(image_id, user_id)
