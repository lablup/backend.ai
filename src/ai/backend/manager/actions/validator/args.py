from dataclasses import dataclass

from .batch import BatchActionValidator
from .scope import ScopeActionValidator
from .single_entity import SingleEntityActionValidator


@dataclass
class ValidatorArgs:
    batch: list[BatchActionValidator]
    scope: list[ScopeActionValidator]
    single_entity: list[SingleEntityActionValidator]
