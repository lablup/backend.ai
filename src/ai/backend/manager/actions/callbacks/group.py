from dataclasses import dataclass

from .callback.batch import BatchActionCallback
from .callback.create import EntityCreateActionCallback
from .callback.scope import ScopedActionCallback
from .callback.single_entity import SingleEntityActionCallback


@dataclass(frozen=True)
class CallbackGroup:
    create: list[EntityCreateActionCallback]
    batch: list[BatchActionCallback]
    single_entity: list[SingleEntityActionCallback]
    scope: list[ScopedActionCallback]
