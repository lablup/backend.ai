import functools
import logging

from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import AgentId, ImageAlias
from ai.backend.common.utils import join_non_empty
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.exceptions import ImageNotFound
from ai.backend.manager.models.image import (
    ImageIdentifier,
    ImageStatus,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitActionResult,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionNoSuchAliasError,
    DealiasImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageActionByIdGenericForbiddenError,
    ForgetImageActionByIdObjectNotFoundError,
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
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
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageActionByIdGenericForbiddenError,
    PurgeImageActionByIdObjectNotFoundError,
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgedImagesData,
    PurgeImageAction,
    PurgeImageActionResult,
    PurgeImagesAction,
    PurgeImagesActionResult,
)
from ai.backend.manager.services.image.actions.scan_image import (
    ScanImageAction,
    ScanImageActionResult,
)
from ai.backend.manager.services.image.actions.unload_image import (
    UnloadImageAction,
    UnloadImageActionResult,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
    UntagImageFromRegistryActionGenericForbiddenError,
    UntagImageFromRegistryActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


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

    async def forget_image(self, action: ForgetImageAction) -> ForgetImageActionResult:
        if action.client_role == UserRole.SUPERADMIN:
            # Superadmin can forget any image without checking ownership
            data = await self._image_repository.soft_delete_image_force(
                [
                    ImageIdentifier(action.reference, action.architecture),
                    ImageAlias(action.reference),
                ],
            )
            return ForgetImageActionResult(image=data)
        # Regular users can only forget images they own
        data = await self._image_repository.soft_delete_user_image(
            [
                ImageIdentifier(action.reference, action.architecture),
                ImageAlias(action.reference),
            ],
            action.user_id,
        )
        return ForgetImageActionResult(image=data)

    async def forget_image_by_id(
        self, action: ForgetImageByIdAction
    ) -> ForgetImageByIdActionResult:
        image_row = await self._image_repository.get_image_by_id(action.image_id, load_aliases=True)
        if not image_row:
            raise ForgetImageActionByIdObjectNotFoundError()
        if action.client_role != UserRole.SUPERADMIN:
            if not image_row.is_owned_by(action.user_id):
                raise ForgetImageActionByIdGenericForbiddenError()
        await self._image_repository.mark_image_as_deleted(image_row.id)
        image_row.status = ImageStatus.DELETED
        return ForgetImageByIdActionResult(image=image_row.to_dataclass())

    async def alias_image(self, action: AliasImageAction) -> AliasImageActionResult:
        try:
            image_id, image_alias = await self._image_repository.add_image_alias(
                action.alias, action.image_canonical, action.architecture
            )
        except UnknownImageReference:
            raise ImageNotFound
        return AliasImageActionResult(
            image_id=image_id,
            image_alias=image_alias.to_dataclass(),
        )

    async def dealias_image(self, action: DealiasImageAction) -> DealiasImageActionResult:
        existing_alias = await self._image_repository.delete_image_alias(action.alias)
        if existing_alias is None:
            raise DealiasImageActionNoSuchAliasError()

        return DealiasImageActionResult(
            image_id=existing_alias.image_id,
            image_alias=existing_alias.to_dataclass(),
        )

    async def modify_image(self, action: ModifyImageAction) -> ModifyImageActionResult:
        props = action.modifier

        try:
            to_update = props.fields_to_update()
            image_row = await self._image_repository.update_image_properties(
                action.target, action.architecture, to_update
            )
        except UnknownImageReference:
            raise ModifyImageActionUnknownImageReferenceError

        return ModifyImageActionResult(image=image_row.to_dataclass())

    async def preload_image(self, action: PreloadImageAction) -> PreloadImageActionResult:
        raise NotImplementedError

    async def unload_image(self, action: UnloadImageAction) -> UnloadImageActionResult:
        raise NotImplementedError

    async def purge_image_by_id(self, action: PurgeImageByIdAction) -> PurgeImageByIdActionResult:
        image_row = await self._image_repository.get_image_by_id(action.image_id, load_aliases=True)
        if not image_row:
            raise PurgeImageActionByIdObjectNotFoundError()
        if action.client_role != UserRole.SUPERADMIN:
            if not image_row.is_owned_by(action.user_id):
                raise PurgeImageActionByIdGenericForbiddenError()
        await self._image_repository.delete_image_with_aliases(action.image_id)
        return PurgeImageByIdActionResult(image=image_row.to_dataclass())

    async def untag_image_from_registry(
        self, action: UntagImageFromRegistryAction
    ) -> UntagImageFromRegistryActionResult:
        image_row = await self._image_repository.untag_image_from_registry(action.image_id)
        if not image_row:
            raise ImageNotFound
        if action.client_role != UserRole.SUPERADMIN:
            if not image_row.is_owned_by(action.user_id):
                raise UntagImageFromRegistryActionGenericForbiddenError()

        return UntagImageFromRegistryActionResult(image=image_row.to_dataclass())

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

            purged_images_data = PurgedImagesData(purged_images=[], agent_id=agent_id)

            results = await self._agent_registry.purge_images(
                AgentId(agent_id),
                PurgeImagesReq(images=image_canonicals, force=force, noprune=noprune),
            )

            for result in results.responses:
                if not result.error:
                    image_canonical = result.image
                    arch = arch_per_images[image_canonical]
                    image_identifier = ImageIdentifier(image_canonical, arch)
                    image_row = await self._image_repository.resolve_image([image_identifier])
                    purged_images_data.purged_images.append(image_canonical)
                    total_reserved_bytes += image_row.size_bytes
                else:
                    errors.append(
                        f"Failed to purge image {image_canonical} from agent {agent_id}: {result.error}"
                    )

            purged_images_data_list.append(purged_images_data)

        return PurgeImagesActionResult(
            purged_images=purged_images_data_list,
            errors=errors,
            total_reserved_bytes=total_reserved_bytes,
        )

    async def scan_image(self, action: ScanImageAction) -> ScanImageActionResult:
        image_canonical = action.canonical
        architecture = action.architecture

        image_row = await self._image_repository.resolve_image(
            [
                ImageIdentifier(image_canonical, architecture),
            ],
        )
        join = functools.partial(join_non_empty, sep="/")
        registry_key = join(
            image_row.registry,
            image_row.project,
        )

        result = await self._image_repository.scan_single_image(
            registry_key, image_row, image_canonical
        )
        return ScanImageActionResult(image=result.images[0], errors=result.errors)

    async def clear_image_custom_resource_limit(
        self, action: ClearImageCustomResourceLimitAction
    ) -> ClearImageCustomResourceLimitActionResult:
        image_row = await self._image_repository.clear_image_custom_resource_limit(
            action.image_canonical, action.architecture
        )
        return ClearImageCustomResourceLimitActionResult(image_data=image_row.to_dataclass())
