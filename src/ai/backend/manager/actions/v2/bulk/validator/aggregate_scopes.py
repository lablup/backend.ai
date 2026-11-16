from typing import override

from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import AtomicBulkActionValidator
from ai.backend.manager.actions.v2.ops.aggregate import AggregateLimits

__all__ = ("AggregateScopeCountValidator",)


class AggregateScopeCountValidator(AtomicBulkActionValidator):
    """Refuses an aggregate naming more scopes than allowed, before any is authorized."""

    _limits: AggregateLimits

    def __init__(self, limits: AggregateLimits) -> None:
        self._limits = limits

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> None:
        self._limits.check_scopes(len(meta.entity_ids))
