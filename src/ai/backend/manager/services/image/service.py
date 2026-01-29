import logging
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import AgentId, ImageAlias
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.image.types import ImageWithAgentInstallStatus
from ai.backend.manager.errors.image import ImageAccessForbiddenError, ImageNotFound
from ai.backend.manager.models.image import (
    ImageIdentifier,
    ImageRow,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
    AliasImageByIdAction,
    AliasImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitActionResult,
    ClearImageCustomResourceLimitByIdAction,
    ClearImageCustomResourceLimitByIdActionResult,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionResult,
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.get_all_images import (
    GetAllImagesAction,
    GetAllImagesActionResult,
)
from ai.backend.manager.services.image.actions.get_image_installed_agents import (
    GetImageInstalledAgentsAction,
    GetImageInstalledAgentsActionResult,
)
from ai.backend.manager.services.image.actions.get_images import (
    GetImageByIdAction,
    GetImageByIdActionResult,
    GetImageByIdentifierAction,
    GetImageByIdentifierActionResult,
    GetImagesByCanonicalsAction,
    GetImagesByCanonicalsActionResult,
    GetImagesByIdsAction,
    GetImagesByIdsActionResult,
)
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageAction,
    ModifyImageActionResult,
    ModifyImageActionUnknownImageReferenceError,
)
from ai.backend.manager.services.image.actions.preload_image import (
    PreloadImageAction,
    PreloadImageActionResult,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgedImagesData,
    PurgeImageAction,
    PurgeImageActionResult,
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
    PurgeImagesAction,
    PurgeImagesActionResult,
)
from ai.backend.manager.services.image.actions.rescan_images_by_id import (
    RescanImagesByIdAction,
    RescanImagesByIdActionResult,
)
from ai.backend.manager.services.image.actions.scan_image import (
    ScanImageAction,
    ScanImageActionResult,
)
from ai.backend.manager.services.image.actions.search_images import (
    SearchImagesAction,
    SearchImagesActionResult,
)
from ai.backend.manager.services.image.actions.set_image_resource_limit_by_id import (
    SetImageResourceLimitByIdAction,
    SetImageResourceLimitByIdActionResult,
)
from ai.backend.manager.services.image.actions.unload_image import (
    UnloadImageAction,
    UnloadImageActionResult,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
    UntagImageFromRegistryActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageService:
    _agent_registry: AgentRegistry
    _image_repository: ImageRepository

    def __init__(
        self,
        agent_registry: AgentRegistry,
        image_repository: ImageRepository,
    ) -> None:
        self._agent_registry = agent_registry
        self._image_repository = image_repository

    async def _validate_image_ownership(self, image_id: UUID, user_id: UUID) -> None:
        """
        Validates that user owns the image.
        Raises ImageAccessForbiddenError if user doesn't own the image.

        Note: Non-customized images are not owned by anyone,
        so ownership validation fails for them.
        """
        if not await self._image_repository.validate_image_ownership(image_id, user_id):
            raise ImageAccessForbiddenError()

    async def get_images_by_canonicals(
        self, action: GetImagesByCanonicalsAction
    ) -> GetImagesByCanonicalsActionResult:
        """
        Deprecated. Use get_images_by_ids instead.
        """
        images_with_agent_install_status: list[
            ImageWithAgentInstallStatus
        ] = await self._image_repository.get_images_by_canonicals(
            action.image_canonicals,
            status_filter=action.image_status,
            requested_by_superadmin=(action.user_role == UserRole.SUPERADMIN),
        )
        return GetImagesByCanonicalsActionResult(
            images_with_agent_install_status=images_with_agent_install_status
        )

    async def get_image_by_identifier(
        self, action: GetImageByIdentifierAction
    ) -> GetImageByIdentifierActionResult:
        """
        Deprecated. Use get_image_by_id instead.
        """
        image_with_agent_install_status: ImageWithAgentInstallStatus = (
            await self._image_repository.get_image_by_identifier(
                action.image_identifier,
                status_filter=action.image_status,
                requested_by_superadmin=(action.user_role == UserRole.SUPERADMIN),
            )
        )
        return GetImageByIdentifierActionResult(
            image_with_agent_install_status=image_with_agent_install_status
        )

    async def get_image_installed_agents(
        self, action: GetImageInstalledAgentsAction
    ) -> GetImageInstalledAgentsActionResult:
        image_ids = action.image_ids
        agent_counts_per_image = await self._image_repository.get_image_installed_agents(image_ids)
        return GetImageInstalledAgentsActionResult(data=agent_counts_per_image)

    async def get_all_images(self, action: GetAllImagesAction) -> GetAllImagesActionResult:
        images = await self._image_repository.get_all_images(status_filter=action.status_filter)
        return GetAllImagesActionResult(data=images)

    async def get_image_by_id(self, action: GetImageByIdAction) -> GetImageByIdActionResult:
        user = current_user()
        is_superadmin = user is not None and user.role == UserRole.SUPERADMIN
        image_with_agent_install_status: ImageWithAgentInstallStatus = (
            await self._image_repository.get_image_by_id(
                action.image_id,
                load_aliases=True,
                status_filter=action.image_status,
                requested_by_superadmin=is_superadmin,
            )
        )
        return GetImageByIdActionResult(
            image_with_agent_install_status=image_with_agent_install_status
        )

    async def forget_image(self, action: ForgetImageAction) -> ForgetImageActionResult:
        """
        Deprecated. Use forget_image_by_id instead.
        """
        identifiers: list[ImageAlias | ImageRef | ImageIdentifier] = [
            ImageIdentifier(action.reference, action.architecture),
            ImageAlias(action.reference),
        ]
        # Regular users need ownership validation
        if action.client_role != UserRole.SUPERADMIN:
            image_data = await self._image_repository.resolve_image(identifiers)
            await self._validate_image_ownership(image_data.id, action.user_id)
        data = await self._image_repository.soft_delete_image(identifiers)
        return ForgetImageActionResult(image=data)

    async def forget_image_by_id(
        self, action: ForgetImageByIdAction
    ) -> ForgetImageByIdActionResult:
        # Regular users need ownership validation
        if action.client_role != UserRole.SUPERADMIN:
            await self._validate_image_ownership(action.image_id, action.user_id)
        data = await self._image_repository.soft_delete_image_by_id(action.image_id)
        return ForgetImageByIdActionResult(image=data)

    async def alias_image(self, action: AliasImageAction) -> AliasImageActionResult:
        """
        Deprecated. Use alias_image_by_id instead.
        """
        try:
            image_id, image_alias = await self._image_repository.add_image_alias(
                action.alias, action.image_canonical, action.architecture
            )
        except UnknownImageReference as e:
            raise ImageNotFound from e
        return AliasImageActionResult(
            image_id=image_id,
            image_alias=image_alias,
        )

    async def dealias_image(self, action: DealiasImageAction) -> DealiasImageActionResult:
        result = await self._image_repository.delete_image_alias(action.alias)
        image_id, alias_data = result
        return DealiasImageActionResult(
            image_id=image_id,
            image_alias=alias_data,
        )

    async def modify_image(self, action: ModifyImageAction) -> ModifyImageActionResult:
        try:
            # Resolve image first to get its ID
            image_data = await self._image_repository.resolve_image([
                ImageIdentifier(action.target, action.architecture),
                ImageAlias(action.target),
            ])
            # Create Updater with resolved image ID
            updater: Updater[ImageRow] = Updater(spec=action.updater_spec, pk_value=image_data.id)
            # Pass Updater to repository
            updated_image_data = await self._image_repository.update_image_properties(updater)
        except UnknownImageReference as e:
            raise ModifyImageActionUnknownImageReferenceError from e

        return ModifyImageActionResult(image=updated_image_data)

    async def purge_image_by_id(self, action: PurgeImageByIdAction) -> PurgeImageByIdActionResult:
        # Regular users need ownership validation
        if action.client_role != UserRole.SUPERADMIN:
            await self._validate_image_ownership(action.image_id, action.user_id)
        image_data = await self._image_repository.delete_image_with_aliases(action.image_id)
        return PurgeImageByIdActionResult(image=image_data)

    async def untag_image_from_registry(
        self, action: UntagImageFromRegistryAction
    ) -> UntagImageFromRegistryActionResult:
        # Regular users need ownership validation
        if action.client_role != UserRole.SUPERADMIN:
            await self._validate_image_ownership(action.image_id, action.user_id)
        image_data = await self._image_repository.untag_image_from_registry(action.image_id)
        return UntagImageFromRegistryActionResult(image=image_data)

    async def purge_image(self, action: PurgeImageAction) -> PurgeImageActionResult:
        force, noprune = action.force, action.noprune
        agent_id = action.agent_id
        image_canonical = action.image.name
        arch = action.image.architecture

        image_identifier = ImageIdentifier(image_canonical, arch)
        image_data = await self._image_repository.resolve_image([image_identifier])

        results = await self._agent_registry.purge_images(
            AgentId(agent_id),
            PurgeImagesReq(images=[image_canonical], force=force, noprune=noprune),
        )

        error = None
        for result in results.responses:
            if result.error:
                error = (
                    f"Failed to purge image {image_canonical} from agent {agent_id}: {result.error}"
                )

        return PurgeImageActionResult(
            purged_image=image_data,
            error=error,
            reserved_bytes=image_data.size_bytes,
        )

    # TODO: The query is incorrectly separated. Need to optimize this.
    async def purge_images(self, action: PurgeImagesAction) -> PurgeImagesActionResult:
        errors = []
        total_reserved_bytes = 0
        force, noprune = action.force, action.noprune

        purged_images_data_list: list[PurgedImagesData] = []
        for key in action.keys:
            agent_id = key.agent_id
            images = key.images

            image_canonicals = [image.name for image in images]
            arch_per_images = {image.name: image.architecture for image in images}

            results = await self._agent_registry.purge_images(
                AgentId(agent_id),
                PurgeImagesReq(images=image_canonicals, force=force, noprune=noprune),
            )

            # Collect successful purges for batch resolution
            successful_identifiers: list[list[ImageIdentifier]] = []
            successful_canonicals = []

            for result in results.responses:
                if not result.error:
                    image_canonical = result.image
                    arch = arch_per_images[image_canonical]
                    successful_identifiers.append([ImageIdentifier(image_canonical, arch)])
                    successful_canonicals.append(image_canonical)
                else:
                    errors.append(
                        f"Failed to purge image {result.image} from agent {agent_id}: {result.error}"
                    )

            # Batch resolve all successful images
            purged_images_data = PurgedImagesData(purged_images=[], agent_id=agent_id)
            if successful_identifiers:
                image_data_list = await self._image_repository.resolve_images_batch(
                    successful_identifiers
                )
                for image_data, canonical in zip(
                    image_data_list, successful_canonicals, strict=True
                ):
                    purged_images_data.purged_images.append(canonical)
                    total_reserved_bytes += image_data.size_bytes

            purged_images_data_list.append(purged_images_data)

        return PurgeImagesActionResult(
            purged_images=purged_images_data_list,
            errors=errors,
            total_reserved_bytes=total_reserved_bytes,
        )

    async def scan_image(self, action: ScanImageAction) -> ScanImageActionResult:
        """
        Deprecated. Use rescan_images_by_id instead.
        """
        image_canonical = action.canonical
        architecture = action.architecture

        result = await self._image_repository.scan_image_by_identifier(
            image_canonical, architecture
        )
        return ScanImageActionResult(image=result.images[0], errors=result.errors)

    async def clear_image_custom_resource_limit(
        self, action: ClearImageCustomResourceLimitAction
    ) -> ClearImageCustomResourceLimitActionResult:
        """
        Deprecated. Use clear_image_custom_resource_limit_by_id instead.
        """
        image_data = await self._image_repository.clear_image_custom_resource_limit(
            action.image_canonical, action.architecture
        )
        return ClearImageCustomResourceLimitActionResult(image_data=image_data)

    async def search_images(self, action: SearchImagesAction) -> SearchImagesActionResult:
        """
        Search images using a batch querier with conditions, pagination, and ordering.
        """
        result = await self._image_repository.search_images(action.querier)
        return SearchImagesActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def alias_image_by_id(self, action: AliasImageByIdAction) -> AliasImageByIdActionResult:
        """
        Creates an alias for an image by its ID.
        """
        image_id, image_alias = await self._image_repository.add_image_alias_by_id(
            action.image_id, action.alias
        )
        return AliasImageByIdActionResult(
            image_id=image_id,
            image_alias=image_alias,
        )

    async def get_images_by_ids(self, action: GetImagesByIdsAction) -> GetImagesByIdsActionResult:
        """
        Retrieves multiple images by their IDs.
        """
        images_with_agent_install_status = await self._image_repository.get_images_by_ids(
            action.image_ids,
            status_filter=action.image_status,
            requested_by_superadmin=(action.user_role == UserRole.SUPERADMIN),
        )
        return GetImagesByIdsActionResult(images=images_with_agent_install_status)

    async def preload_image(self, action: PreloadImageAction) -> PreloadImageActionResult:
        """
        Preloads images by their IDs to specified agents.
        """
        raise NotImplementedError

    async def unload_image(self, action: UnloadImageAction) -> UnloadImageActionResult:
        """
        Unloads images by their IDs from specified agents.
        """
        raise NotImplementedError

    async def clear_image_custom_resource_limit_by_id(
        self, action: ClearImageCustomResourceLimitByIdAction
    ) -> ClearImageCustomResourceLimitByIdActionResult:
        """
        Clears custom resource limits for an image by its ID.
        """
        image_data = await self._image_repository.clear_image_resource_limits_by_id(action.image_id)
        return ClearImageCustomResourceLimitByIdActionResult(image_data=image_data)

    async def rescan_images_by_id(
        self, action: RescanImagesByIdAction
    ) -> RescanImagesByIdActionResult:
        """
        Rescans images by their IDs.
        """
        result = await self._image_repository.scan_images_by_ids(action.image_ids)
        return RescanImagesByIdActionResult(images=result.images, errors=result.errors)

    async def set_image_resource_limit_by_id(
        self, action: SetImageResourceLimitByIdAction
    ) -> SetImageResourceLimitByIdActionResult:
        """
        Sets resource limit for an image by its ID.
        """
        image_data = await self._image_repository.set_image_resource_limit_by_id(
            action.image_id,
            action.resource_limit,
        )
        return SetImageResourceLimitByIdActionResult(image_data=image_data)
