from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
)
from ai.backend.manager.services.image.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
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
from ai.backend.manager.services.image.actions.modify_image import (
    ModifyImageAction,
    ModifyImageActionResult,
)
from ai.backend.manager.services.image.actions.preload_image import (
    PreloadImageAction,
    PreloadImageActionResult,
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
from ai.backend.manager.services.image.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)
from ai.backend.manager.services.image.actions.unload_image import (
    UnloadImageAction,
    UnloadImageActionResult,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
    UntagImageFromRegistryActionResult,
)

from .service import ImageService


class ImageProcessors:
    forget_image: ActionProcessor[ForgetImageAction, ForgetImageActionResult]
    forget_image_by_id: ActionProcessor[ForgetImageByIdAction, ForgetImageByIdActionResult]
    purge_image_by_id: ActionProcessor[PurgeImageByIdAction, PurgeImageByIdActionResult]
    alias_image: ActionProcessor[AliasImageAction, AliasImageActionResult]
    dealias_image: ActionProcessor[DealiasImageAction, DealiasImageActionResult]
    clear_images: ActionProcessor[ClearImagesAction, ClearImagesActionResult]
    modify_image: ActionProcessor[ModifyImageAction, ModifyImageActionResult]
    preload_image: ActionProcessor[PreloadImageAction, PreloadImageActionResult]
    unload_image: ActionProcessor[UnloadImageAction, UnloadImageActionResult]
    untag_image_from_registry: ActionProcessor[
        UntagImageFromRegistryAction, UntagImageFromRegistryActionResult
    ]
    rescan_images: ActionProcessor[RescanImagesAction, RescanImagesActionResult]
    purge_image: ActionProcessor[PurgeImageAction, PurgeImageActionResult]
    purge_images: ActionProcessor[PurgeImagesAction, PurgeImagesActionResult]

    def __init__(self, service: ImageService) -> None:
        self.forget_image = ActionProcessor(service.forget_image)
        self.forget_image_by_id = ActionProcessor(service.forget_image_by_id)
        self.purge_image_by_id = ActionProcessor(service.purge_image_by_id)
        self.alias_image = ActionProcessor(service.alias_image)
        self.dealias_image = ActionProcessor(service.dealias_image)
        self.clear_images = ActionProcessor(service.clear_images)
        self.modify_image = ActionProcessor(service.modify_image)
        self.preload_image = ActionProcessor(service.preload_image)
        self.unload_image = ActionProcessor(service.unload_image)
        self.untag_image_from_registry = ActionProcessor(service.untag_image_from_registry)
        self.rescan_images = ActionProcessor(service.rescan_images)
        self.purge_image = ActionProcessor(service.purge_image)
        self.purge_images = ActionProcessor(service.purge_images)
