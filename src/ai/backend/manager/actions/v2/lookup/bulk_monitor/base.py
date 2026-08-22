from abc import ABC

from ai.backend.manager.actions.v2.lookup.bulk_result import BulkLookupActionProcessResult
from ai.backend.manager.actions.v2.lookup.bulk_trigger import BulkLookupActionTriggerMeta

__all__ = ("BulkLookupActionMonitor",)


class BulkLookupActionMonitor(ABC):
    """Observes the lifecycle of a bulk lookup run."""

    async def prepare(self, meta: BulkLookupActionTriggerMeta) -> None:
        raise NotImplementedError("Subclasses must implement the prepare method")

    async def done(
        self, meta: BulkLookupActionTriggerMeta, result: BulkLookupActionProcessResult
    ) -> None:
        raise NotImplementedError("Subclasses must implement the done method")
