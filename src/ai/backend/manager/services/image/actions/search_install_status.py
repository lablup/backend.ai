from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageWithAgentInstallStatus
from ai.backend.manager.models.image.searchers import ImageSearcher
from ai.backend.manager.services.image.actions.base import ImageScopeAction, ImageScopeActionResult


@dataclass
class SearchImagesWithInstallStatusAction(ImageScopeAction):
    """Page through the images the named scopes reach, each with where it is installed.

    One action for every such read: a read by id, by canonical name or across the whole
    catalog differ in the searcher's conditions, not in what they are allowed to see.
    """

    searcher: ImageSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_images_with_install_status"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchImagesWithInstallStatusActionResult(ImageScopeActionResult):
    items: list[ImageWithAgentInstallStatus]
