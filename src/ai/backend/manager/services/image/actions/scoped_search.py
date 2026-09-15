"""Image search over the scopes images are reachable from."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.ops.base import ScopeItem
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.image.scopes import (
    ContainerRegistryImageOperationScope,
    DomainImageOperationScope,
    GlobalImageOperationScope,
    ProjectImageOperationScope,
    UserImageOperationScope,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.image.actions.base import (
    ImageScopeAction,
    ImageScopeActionResult,
)

__all__ = (
    "ContainerRegistryImageScopeItem",
    "DomainImageScopeItem",
    "ImageScopeItem",
    "ProjectImageScopeItem",
    "ScopedSearchImagesAction",
    "ScopedSearchImagesActionResult",
    "UserImageScopeItem",
)


class ImageScopeItem(ScopeItem, ABC):
    """One side an image is reachable from."""


@dataclass(frozen=True)
class DomainImageScopeItem(ImageScopeItem):
    """The images of one domain."""

    domain_id: DomainID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def operation_scope(self) -> OperationScope:
        return DomainImageOperationScope(domain_id=self.domain_id)


@dataclass(frozen=True)
class ProjectImageScopeItem(ImageScopeItem):
    """The images of one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def operation_scope(self) -> OperationScope:
        return ProjectImageOperationScope(project_id=self.project_id)


@dataclass(frozen=True)
class UserImageScopeItem(ImageScopeItem):
    """The images one user reaches."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return UserImageOperationScope(user_id=self.user_id)


@dataclass(frozen=True)
class ContainerRegistryImageScopeItem(ImageScopeItem):
    """The images of one container registry."""

    registry_id: ContainerRegistryID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.registry_id

    @override
    def operation_scope(self) -> OperationScope:
        return ContainerRegistryImageOperationScope(registry_id=self.registry_id)


@dataclass
class ScopedSearchImagesAction(ImageScopeAction):
    """Page through the images the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest. ``include_global`` names no
    scope and is authorized against none: a registry marked global shows its images to
    everyone.
    """

    items: Sequence[ImageScopeItem]
    include_global: bool
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    def operation_scopes(self) -> Sequence[OperationScope]:
        scopes: list[OperationScope] = [item.operation_scope() for item in self.items]
        if self.include_global:
            scopes.append(GlobalImageOperationScope())
        return scopes

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_images"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ScopedSearchImagesActionResult(ImageScopeActionResult):
    data: list[ImageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
