from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.bulk import BaseBulkAction


@dataclass(frozen=True)
class DeniedEntity:
    """A bulk entity that a validator rejected, paired with its reason."""

    entity_id: str
    deny_reason: str


@dataclass(frozen=True)
class BulkValidationResult:
    """Per-entity validation outcome for a bulk action.

    ``BulkActionProcessor`` intersects ``allowed_entity_ids`` across
    validators and records each ``DeniedEntity`` — with its reason — on the
    corresponding ``BulkValidatorDecision`` so the final response can
    surface *why* each ID was filtered out.
    """

    allowed_entity_ids: list[str]
    denied_entities: list[DeniedEntity]


class BulkActionValidator(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Stable identifier used in ``BulkValidatorDecision.validator_name``.

        Chosen by the implementation so logs and partial-success responses can
        attribute denials to a specific validator independently of the Python
        class name.
        """
        raise NotImplementedError

    @abstractmethod
    async def validate(
        self, action: BaseBulkAction[Any], meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        """Validate the bulk action and return per-entity permission results.

        Implementations must classify every ID in ``action.entity_ids`` as
        either allowed or denied. Validators that cannot make a decision for
        an ID should treat it as allowed.

        The processor wraps each call in its own async context manager so
        cross-cutting concerns (timing, audit) live in one place — validators
        do not need to own them.
        """
        raise NotImplementedError
