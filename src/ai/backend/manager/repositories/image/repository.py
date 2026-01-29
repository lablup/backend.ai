from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from ai.backend.common.bgtask.reporter import ProgressReporter
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
    ImageAliasListResult,
    ImageData,
    ImageDataWithDetails,
    ImageListResult,
    ImageStatus,
    ImageWithAgentInstallStatus,
    RescanImagesResult,
    ResourceLimitInput,
)
from ai.backend.manager.models.image import (
    ImageIdentifier,
    ImageRow,
)
from ai.backend.manager.models.image.row import ImageAliasRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, Creator
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
        status_filter: list[ImageStatus] | None = None,
        hide_agents: bool = False,
    ) -> list[ImageWithAgentInstallStatus]:
        """
        Deprecated. Use get_images_by_ids instead.
        """
        images_data = await self._db_source.query_images_by_canonicals(
            image_canonicals, status_filter
        )
        image_ids = list(images_data.keys())
        installed_agents_for_images = await self._stateful_source.list_agents_with_images(image_ids)

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
        status_filter: list[ImageStatus] | None = None,
        hide_agents: bool = False,
    ) -> ImageWithAgentInstallStatus:
        """
        Deprecated. Use get_image_by_id instead.
        """
        image_data: ImageDataWithDetails = await self._db_source.query_image_details_by_identifier(
            identifier, status_filter
        )
        installed_agents = await self._stateful_source.list_agents_with_image(image_data.id)

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
        status_filter: list[ImageStatus] | None = None,
        hide_agents: bool = False,
    ) -> ImageWithAgentInstallStatus:
        image_data: ImageDataWithDetails = await self._db_source.query_image_details_by_id(
            image_id, load_aliases, status_filter
        )
        installed_agents = await self._stateful_source.list_agents_with_image(image_data.id)

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
        self, status_filter: list[ImageStatus] | None = None
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
    async def soft_delete_image(
        self,
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier],
    ) -> ImageData:
        """
        Deprecated. Use soft_delete_image_by_id instead.
        """
        return await self._db_source.mark_image_deleted(identifiers)

    @image_repository_resilience.apply()
    async def soft_delete_image_by_id(
        self,
        image_id: UUID,
    ) -> ImageData:
        """
        Marks an image as deleted by its ID.
        """
        return await self._db_source.mark_image_deleted_by_id(image_id)

    @image_repository_resilience.apply()
    async def fetch_image_by_id(self, image_id: UUID, load_aliases: bool = False) -> ImageData:
        """
        Fetches an image from database by ID.
        Raises ImageNotFound if image doesn't exist.
        """
        return await self._db_source.fetch_image_by_id(image_id, load_aliases)

    @image_repository_resilience.apply()
    async def validate_image_ownership(self, image_id: UUID, user_id: UUID) -> bool:
        """
        Validates that user owns the image.
        Returns True if user owns the image, False otherwise.
        Raises ImageNotFound if image doesn't exist.
        """
        return await self._db_source.validate_image_ownership(image_id, user_id)

    @image_repository_resilience.apply()
    async def add_image_alias(
        self, alias: str, image_canonical: str, architecture: str
    ) -> tuple[UUID, ImageAliasData]:
        """
        Deprecated. Use add_image_alias_by_id instead.
        """
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
        Deprecated. Use scan_images_by_ids instead.
        """
        return await self._db_source.scan_and_upsert_image(image_canonical, architecture)

    @image_repository_resilience.apply()
    async def untag_image_from_registry(self, image_id: UUID) -> ImageData:
        return await self._db_source.remove_tag_from_registry(image_id)

    @image_repository_resilience.apply()
    async def update_image_properties(self, updater: Updater[ImageRow]) -> ImageData:
        return await self._db_source.modify_image_properties(updater)

    @image_repository_resilience.apply()
    async def clear_image_custom_resource_limit(
        self, image_canonical: str, architecture: str
    ) -> ImageData:
        """
        Deprecated. Use clear_image_resource_limits_by_id instead.
        """
        return await self._db_source.clear_image_resource_limits(image_canonical, architecture)

    @image_repository_resilience.apply()
    async def add_image_alias_by_id(self, creator: Creator[ImageAliasRow]) -> ImageAliasData:
        """
        Creates an image alias using the Creator pattern.
        """
        return await self._db_source.insert_image_alias_by_id(creator)

    @image_repository_resilience.apply()
    async def get_images_by_ids(
        self,
        image_ids: list[UUID],
        status_filter: list[ImageStatus] | None = None,
        hide_agents: bool = False,
    ) -> list[ImageWithAgentInstallStatus]:
        """
        Retrieves multiple images by their IDs with agent install status.
        """
        images_data = await self._db_source.query_images_by_ids(image_ids, status_filter)
        image_id_list = list(images_data.keys())
        installed_agents_for_images = await self._stateful_source.list_agents_with_images(
            image_id_list
        )

        images_with_agent_install_status: list[ImageWithAgentInstallStatus] = []
        for image_id_key, image in images_data.items():
            installed_agents = installed_agents_for_images.get(image_id_key, set())
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
    async def clear_image_resource_limits_by_id(self, image_id: UUID) -> ImageData:
        """
        Clears image resource limits by image ID.
        """
        return await self._db_source.clear_image_resource_limits_by_id(image_id)

    @image_repository_resilience.apply()
    async def set_image_resource_limit_by_id(
        self,
        image_id: UUID,
        resource_limit: ResourceLimitInput,
    ) -> ImageData:
        """
        Sets resource limit for an image by its ID.
        """
        return await self._db_source.set_image_resource_limit_by_id(image_id, resource_limit)

    @image_repository_resilience.apply()
    async def scan_images_by_ids(self, image_ids: list[UUID]) -> RescanImagesResult:
        """
        Scans multiple images by their IDs.
        """
        return await self._db_source.scan_images_by_ids(image_ids)

    @image_repository_resilience.apply()
    async def delete_image_with_aliases(self, image_id: UUID) -> ImageData:
        """
        Deletes an image and all its aliases.
        """
        return await self._db_source.remove_image_and_aliases(image_id)

    @image_repository_resilience.apply()
    async def search_images(self, querier: BatchQuerier) -> ImageListResult:
        """
        Search images using a batch querier with conditions, pagination, and ordering.
        Returns ImageListResult with items and pagination info.
        """
        return await self._db_source.search_images(querier)

    @image_repository_resilience.apply()
    async def search_aliases(self, querier: BatchQuerier) -> ImageAliasListResult:
        """
        Search image aliases using a batch querier with conditions, pagination, and ordering.
        Returns ImageAliasListResult with items and pagination info.
        """
        return await self._db_source.search_aliases(querier)

    @image_repository_resilience.apply()
    async def rescan_images(
        self,
        registry_or_image: str | None = None,
        project: str | None = None,
        *,
        reporter: ProgressReporter | None = None,
    ) -> RescanImagesResult:
        """
        Rescan container registries and update images table.

        If registry name is provided for `registry_or_image`, scans all images in the specified registry.
        If image canonical name is provided for `registry_or_image`, only scan the image.
        If the `registry_or_image` is not provided, scan all configured registries.

        If `project` is provided, only scan the registries associated with the project.
        """
        return await self._db_source.rescan_images(
            registry_or_image,
            project,
            reporter=reporter,
        )
