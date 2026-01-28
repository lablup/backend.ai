from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
)
from ai.backend.manager.services.image.actions.alias_image_by_id import (
    AliasImageByIdAction,
    AliasImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitActionResult,
)
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit_by_id import (
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
)
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.get_all_images import (
    GetAllImagesAction,
    GetAllImagesActionResult,
)
from ai.backend.manager.services.image.actions.get_image_by_id import (
    GetImageByIdAction,
    GetImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.get_image_by_identifier import (
    GetImageByIdentifierAction,
    GetImageByIdentifierActionResult,
)
from ai.backend.manager.services.image.actions.get_image_installed_agents import (
    GetImageInstalledAgentsAction,
    GetImageInstalledAgentsActionResult,
)
from ai.backend.manager.services.image.actions.get_images_by_canonicals import (
    GetImagesByCanonicalsAction,
    GetImagesByCanonicalsActionResult,
)
from ai.backend.manager.services.image.actions.get_images_by_ids import (
    GetImagesByIdsAction,
    GetImagesByIdsActionResult,
)
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageAction,
    ModifyImageActionResult,
)
from ai.backend.manager.services.image.actions.preload_image_by_id import (
    PreloadImageByIdAction,
    PreloadImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.purge_images import (
    PurgeImageAction,
    PurgeImageActionResult,
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
from ai.backend.manager.services.image.actions.unload_image_by_id import (
    UnloadImageByIdAction,
    UnloadImageByIdActionResult,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
    UntagImageFromRegistryActionResult,
)

from .service import ImageService


class ImageProcessors(AbstractProcessorPackage):
    forget_image: ActionProcessor[ForgetImageAction, ForgetImageActionResult]
    forget_image_by_id: ActionProcessor[ForgetImageByIdAction, ForgetImageByIdActionResult]
    purge_image_by_id: ActionProcessor[PurgeImageByIdAction, PurgeImageByIdActionResult]
    alias_image: ActionProcessor[AliasImageAction, AliasImageActionResult]
    alias_image_by_id: ActionProcessor[AliasImageByIdAction, AliasImageByIdActionResult]
    dealias_image: ActionProcessor[DealiasImageAction, DealiasImageActionResult]
    modify_image: ActionProcessor[ModifyImageAction, ModifyImageActionResult]
    preload_image_by_id: ActionProcessor[PreloadImageByIdAction, PreloadImageByIdActionResult]
    unload_image_by_id: ActionProcessor[UnloadImageByIdAction, UnloadImageByIdActionResult]
    untag_image_from_registry: ActionProcessor[
        UntagImageFromRegistryAction, UntagImageFromRegistryActionResult
    ]
    scan_image: ActionProcessor[ScanImageAction, ScanImageActionResult]
    purge_image: ActionProcessor[PurgeImageAction, PurgeImageActionResult]
    purge_images: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]
    clear_image_custom_resource_limit: ActionProcessor[
        ClearImageCustomResourceLimitAction,
        ClearImageCustomResourceLimitActionResult,
    ]
    clear_image_custom_resource_limit_by_id: ActionProcessor[
        ClearImageCustomResourceLimitByIdAction,
        ClearImageCustomResourceLimitByIdActionResult,
    ]
    rescan_images_by_id: ActionProcessor[RescanImagesByIdAction, RescanImagesByIdActionResult]
    set_image_resource_limit_by_id: ActionProcessor[
        SetImageResourceLimitByIdAction, SetImageResourceLimitByIdActionResult
    ]
    get_image_by_id: ActionProcessor[GetImageByIdAction, GetImageByIdActionResult]
    get_image_by_identifier: ActionProcessor[
        GetImageByIdentifierAction, GetImageByIdentifierActionResult
    ]
    get_images_by_canonicals: ActionProcessor[
        GetImagesByCanonicalsAction, GetImagesByCanonicalsActionResult
    ]
    get_images_by_ids: ActionProcessor[GetImagesByIdsAction, GetImagesByIdsActionResult]
    get_image_installed_agents: ActionProcessor[
        GetImageInstalledAgentsAction, GetImageInstalledAgentsActionResult
    ]
    get_all_images: ActionProcessor[GetAllImagesAction, GetAllImagesActionResult]
    search_images: ActionProcessor[SearchImagesAction, SearchImagesActionResult]

    def __init__(self, service: ImageService, action_monitors: list[ActionMonitor]) -> None:
        self.get_image_installed_agents = ActionProcessor(
            service.get_image_installed_agents, action_monitors
        )
        self.get_all_images = ActionProcessor(service.get_all_images, action_monitors)
        self.get_images_by_canonicals = ActionProcessor(
            service.get_images_by_canonicals, action_monitors
        )
        self.get_images_by_ids = ActionProcessor(service.get_images_by_ids, action_monitors)
        self.get_image_by_identifier = ActionProcessor(
            service.get_image_by_identifier, action_monitors
        )
        self.get_image_by_id = ActionProcessor(service.get_image_by_id, action_monitors)
        self.forget_image = ActionProcessor(service.forget_image, action_monitors)
        self.forget_image_by_id = ActionProcessor(service.forget_image_by_id, action_monitors)
        self.purge_image_by_id = ActionProcessor(service.purge_image_by_id, action_monitors)
        self.alias_image = ActionProcessor(service.alias_image, action_monitors)
        self.alias_image_by_id = ActionProcessor(service.alias_image_by_id, action_monitors)
        self.dealias_image = ActionProcessor(service.dealias_image, action_monitors)
        self.modify_image = ActionProcessor(service.modify_image, action_monitors)
        self.preload_image_by_id = ActionProcessor(service.preload_image_by_id, action_monitors)
        self.unload_image_by_id = ActionProcessor(service.unload_image_by_id, action_monitors)
        self.untag_image_from_registry = ActionProcessor(
            service.untag_image_from_registry, action_monitors
        )
        self.scan_image = ActionProcessor(service.scan_image, action_monitors)
        self.purge_image = ActionProcessor(service.purge_image, action_monitors)
        self.purge_images = ActionProcessor(service.purge_images, action_monitors)
        self.clear_image_custom_resource_limit = ActionProcessor(
            service.clear_image_custom_resource_limit, action_monitors
        )
        self.clear_image_custom_resource_limit_by_id = ActionProcessor(
            service.clear_image_custom_resource_limit_by_id, action_monitors
        )
        self.rescan_images_by_id = ActionProcessor(service.rescan_images_by_id, action_monitors)
        self.set_image_resource_limit_by_id = ActionProcessor(
            service.set_image_resource_limit_by_id, action_monitors
        )
        self.search_images = ActionProcessor(service.search_images, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ForgetImageAction.spec(),
            ForgetImageByIdAction.spec(),
            PurgeImageByIdAction.spec(),
            AliasImageAction.spec(),
            AliasImageByIdAction.spec(),
            DealiasImageAction.spec(),
            ModifyImageAction.spec(),
            PreloadImageByIdAction.spec(),
            UnloadImageByIdAction.spec(),
            UntagImageFromRegistryAction.spec(),
            ScanImageAction.spec(),
            PurgeImagesAction.spec(),
            ClearImageCustomResourceLimitAction.spec(),
            ClearImageCustomResourceLimitByIdAction.spec(),
            RescanImagesByIdAction.spec(),
            SetImageResourceLimitByIdAction.spec(),
            GetImagesByIdsAction.spec(),
        ]
