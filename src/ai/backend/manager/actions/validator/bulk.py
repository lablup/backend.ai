from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.bulk import BaseBulkAction
from ai.backend.manager.data.permission.types import RBACElementRef


@dataclass(frozen=True)
class DeniedEntity:
    """A bulk entity that a validator rejected, paired with its reason."""

    entity_ref: RBACElementRef
    deny_reason: str


@dataclass(frozen=True)
class BulkValidationResult:
    """Per-entity validation outcome for a bulk action."""

    allowed_entities: list[RBACElementRef]
    denied_entities: list[DeniedEntity]


class BulkActionValidator(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Stable identifier for ``ValidatorDecision.validator_name``."""
        raise NotImplementedError

    @abstractmethod
    async def validate(
        self, action: BaseBulkAction[Any], meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        """Classify each target in ``action.targets()`` as allowed or denied."""
        raise NotImplementedError
