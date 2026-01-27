from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator

TCreatorSpec = TypeVar("TCreatorSpec", bound=CreatorSpec)


class CreatorAdapter[TCreatorSpec: CreatorSpec](ABC):
    @abstractmethod
    def build(self, spec: TCreatorSpec) -> RBACEntityCreator:
        pass
