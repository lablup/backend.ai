from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.image.types import ImageData
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
)
from ai.backend.manager.services.image.actions.preload_image import (
    PreloadImageAction,
    PreloadImageActionResult,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImageAction,
    PurgeImageActionResult,
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
    PurgeImagesAction,
    PurgeImagesActionResult,
)
from ai.backend.manager.services.image.actions.restore_image import (
    RestoreImageByIdAction,
    RestoreImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.scan_image import (
    ScanImageAction,
    ScanImageActionResult,
)
from ai.backend.manager.services.image.actions.search_aliases import (
    SearchAliasesAction,
    SearchAliasesActionResult,
)
from ai.backend.manager.services.image.actions.search_images import (
    SearchImagesAction,
    SearchImagesActionResult,
)
from ai.backend.manager.services.image.actions.set_image_resource_limit import (
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
from ai.backend.manager.services.image.actions.update_image import (
    UpdateImageAction,
    UpdateImageActionResult,
)
from ai.backend.manager.services.image.actions.update_image_by_id import (
    UpdateImageByIdAction,
    UpdateImageByIdActionResult,
)

from .service import ImageService


class ImageProcessors:
    forget_image: GlobalActionProcessor[ForgetImageAction, ForgetImageActionResult]
    forget_image_by_id: SingleEntityActionProcessor[
        ForgetImageByIdAction, ForgetImageByIdActionResult
    ]
    restore_image_by_id: SingleEntityActionProcessor[
        RestoreImageByIdAction, RestoreImageByIdActionResult
    ]
    purge_image_by_id: SingleEntityActionProcessor[PurgeImageByIdAction, PurgeImageByIdActionResult]
    alias_image: GlobalActionProcessor[AliasImageAction, AliasImageActionResult]
    alias_image_by_id: GlobalActionProcessor[AliasImageByIdAction, AliasImageByIdActionResult]
    dealias_image: GlobalActionProcessor[DealiasImageAction, DealiasImageActionResult]
    update_image: GlobalActionProcessor[UpdateImageAction, UpdateImageActionResult]
    update_image_by_id: GlobalActionProcessor[UpdateImageByIdAction, UpdateImageByIdActionResult]
    preload_image: GlobalActionProcessor[PreloadImageAction, PreloadImageActionResult]
    unload_image: GlobalActionProcessor[UnloadImageAction, UnloadImageActionResult]
    untag_image_from_registry: GlobalActionProcessor[
        UntagImageFromRegistryAction, UntagImageFromRegistryActionResult
    ]
    scan_image: GlobalActionProcessor[ScanImageAction, ScanImageActionResult]
    purge_image: GlobalActionProcessor[PurgeImageAction, PurgeImageActionResult]
    purge_images: GlobalActionProcessor[PurgeImagesAction, PurgeImagesActionResult]
    clear_image_custom_resource_limit: GlobalActionProcessor[
        ClearImageCustomResourceLimitAction,
        ClearImageCustomResourceLimitActionResult,
    ]
    clear_image_custom_resource_limit_by_id: GlobalActionProcessor[
        ClearImageCustomResourceLimitByIdAction,
        ClearImageCustomResourceLimitByIdActionResult,
    ]
    set_image_resource_limit_by_id: GlobalActionProcessor[
        SetImageResourceLimitByIdAction, SetImageResourceLimitByIdActionResult
    ]
    get_image_by_id: GlobalActionProcessor[GetImageByIdAction, GetImageByIdActionResult]
    get_image_by_identifier: GlobalActionProcessor[
        GetImageByIdentifierAction, GetImageByIdentifierActionResult
    ]
    get_images_by_canonicals: GlobalActionProcessor[
        GetImagesByCanonicalsAction, GetImagesByCanonicalsActionResult
    ]
    get_image_installed_agents: GlobalActionProcessor[
        GetImageInstalledAgentsAction, GetImageInstalledAgentsActionResult
    ]
    get_all_images: GlobalActionProcessor[GetAllImagesAction, GetAllImagesActionResult]
    search_images: GlobalActionProcessor[SearchImagesAction, SearchImagesActionResult]
    search_aliases: GlobalActionProcessor[SearchAliasesAction, SearchAliasesActionResult]

    def __init__(self, group: ProcessorGroup[ImageData], service: ImageService) -> None:
        # Actions without RBAC validation (internal/system or special entity types)
        self.get_image_installed_agents = group.global_scope(
            GetImageInstalledAgentsAction, service.get_image_installed_agents
        )
        self.get_images_by_canonicals = group.global_scope(
            GetImagesByCanonicalsAction, service.get_images_by_canonicals
        )
        self.get_image_by_identifier = group.global_scope(
            GetImageByIdentifierAction, service.get_image_by_identifier
        )
        self.get_image_by_id = group.global_scope(GetImageByIdAction, service.get_image_by_id)
        self.forget_image = group.global_scope(ForgetImageAction, service.forget_image)

        self.get_all_images = group.global_scope(GetAllImagesAction, service.get_all_images)
        self.search_images = group.global_scope(SearchImagesAction, service.search_images)

        self.forget_image_by_id = group.single_entity(
            ForgetImageByIdAction, service.forget_image_by_id
        )
        self.restore_image_by_id = group.single_entity(
            RestoreImageByIdAction, service.restore_image_by_id
        )
        self.purge_image_by_id = group.single_entity(
            PurgeImageByIdAction, service.purge_image_by_id
        )
        # Superadmin-only mutations — access is enforced by check_admin_only at the API layer,
        # so per-entity RBAC validation is not required here.
        self.alias_image = group.global_scope(AliasImageAction, service.alias_image)
        self.alias_image_by_id = group.global_scope(AliasImageByIdAction, service.alias_image_by_id)
        self.dealias_image = group.global_scope(DealiasImageAction, service.dealias_image)
        self.update_image = group.global_scope(UpdateImageAction, service.update_image)
        self.update_image_by_id = group.global_scope(
            UpdateImageByIdAction, service.update_image_by_id
        )
        self.preload_image = group.global_scope(PreloadImageAction, service.preload_image)
        self.unload_image = group.global_scope(UnloadImageAction, service.unload_image)
        self.untag_image_from_registry = group.global_scope(
            UntagImageFromRegistryAction, service.untag_image_from_registry
        )
        self.scan_image = group.global_scope(ScanImageAction, service.scan_image)
        self.purge_image = group.global_scope(PurgeImageAction, service.purge_image)
        self.purge_images = group.global_scope(PurgeImagesAction, service.purge_images)
        self.clear_image_custom_resource_limit = group.global_scope(
            ClearImageCustomResourceLimitAction, service.clear_image_custom_resource_limit
        )
        self.clear_image_custom_resource_limit_by_id = group.global_scope(
            ClearImageCustomResourceLimitByIdAction, service.clear_image_custom_resource_limit_by_id
        )
        self.set_image_resource_limit_by_id = group.global_scope(
            SetImageResourceLimitByIdAction, service.set_image_resource_limit_by_id
        )
        self.search_aliases = group.global_scope(SearchAliasesAction, service.search_aliases)
