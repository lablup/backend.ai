from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.exceptions import BaseActionException
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.models.base import Unset
from ai.backend.manager.services.image.base import ImageAction
from ai.backend.manager.services.image.types import KVPairInput, ResourceLimitInput


@dataclass
class ModifyImageInputData:
    name: Optional[str] = None
    registry: Optional[str] = None
    image: Optional[str] = None
    tag: Optional[str] = None
    architecture: Optional[str] = None
    is_local: Optional[bool] = None
    size_bytes: Optional[int] = None
    type: Optional[str] = None
    digest: Optional[str] = None
    labels: Optional[list[KVPairInput]] = None
    supported_accelerators: Optional[list[str]] | Unset = None
    resource_limits: Optional[list[ResourceLimitInput]] = None


@dataclass
class ModifyImageAction(ImageAction):
    target: str
    architecture: str
    props: ModifyImageInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "modify_image"


@dataclass
class ModifyImageActionResult(BaseActionResult):
    image: ImageData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.image.id)


class ModifyImageActionUnknownImageReferenceError(BaseActionException):
    pass


# TODO: Remove this.
class ModifyImageActionValueError(BaseActionException):
    pass
