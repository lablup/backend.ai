from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
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
    UntagImageFromRegistryActionResult,
)

from .service import ImageService


class ImageProcessors(AbstractProcessorPackage):
    forget_image: ActionProcessor[ForgetImageAction, ForgetImageActionResult]
    forget_image_by_id: ActionProcessor[ForgetImageByIdAction, ForgetImageByIdActionResult]
    purge_image_by_id: ActionProcessor[PurgeImageByIdAction, PurgeImageByIdActionResult]
    alias_image: ActionProcessor[AliasImageAction, AliasImageActionResult]
    dealias_image: ActionProcessor[DealiasImageAction, DealiasImageActionResult]
    modify_image: ActionProcessor[ModifyImageAction, ModifyImageActionResult]
    preload_image: ActionProcessor[PreloadImageAction, PreloadImageActionResult]
    unload_image: ActionProcessor[UnloadImageAction, UnloadImageActionResult]
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

    def __init__(self, service: ImageService, action_monitors: list[ActionMonitor]) -> None:
        self.forget_image = ActionProcessor(service.forget_image, action_monitors)
        self.forget_image_by_id = ActionProcessor(service.forget_image_by_id, action_monitors)
        self.purge_image_by_id = ActionProcessor(service.purge_image_by_id, action_monitors)
        self.alias_image = ActionProcessor(service.alias_image, action_monitors)
        self.dealias_image = ActionProcessor(service.dealias_image, action_monitors)
        self.modify_image = ActionProcessor(service.modify_image, action_monitors)
        self.preload_image = ActionProcessor(service.preload_image, action_monitors)
        self.unload_image = ActionProcessor(service.unload_image, action_monitors)
        self.untag_image_from_registry = ActionProcessor(
            service.untag_image_from_registry, action_monitors
        )
        self.scan_image = ActionProcessor(service.scan_image, action_monitors)
        self.purge_image = ActionProcessor(service.purge_image, action_monitors)
        self.purge_images = ActionProcessor(service.purge_images, action_monitors)
        self.clear_image_custom_resource_limit = ActionProcessor(
            service.clear_image_custom_resource_limit, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            ForgetImageAction.spec(),
            ForgetImageByIdAction.spec(),
            PurgeImageByIdAction.spec(),
            AliasImageAction.spec(),
            DealiasImageAction.spec(),
            ModifyImageAction.spec(),
            PreloadImageAction.spec(),
            UnloadImageAction.spec(),
            UntagImageFromRegistryAction.spec(),
            ScanImageAction.spec(),
            PurgeImagesAction.spec(),
            ClearImageCustomResourceLimitAction.spec(),
        ]
