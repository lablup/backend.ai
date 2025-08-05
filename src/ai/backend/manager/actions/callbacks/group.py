from dataclasses import dataclass

from .callback.batch import BatchActionCallback
from .callback.create import CreateActionCallback
from .callback.scope import ScopedActionCallback
from .callback.single_entity import SingleEntityActionCallback


@dataclass(frozen=True)
class CallbackGroup:
    create: list[CreateActionCallback]
    batch: list[BatchActionCallback]
    single_entity: list[SingleEntityActionCallback]
    scope: list[ScopedActionCallback]
