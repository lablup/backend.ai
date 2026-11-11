"""The bounds an aggregate request is held to."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ai.backend.manager.errors.api import AggregateLimitExceeded
from ai.backend.manager.models.specs.aggregate.aggregator import Aggregator

__all__ = ("AggregateLimits",)


@dataclass(frozen=True)
class AggregateLimits:
    """Set from ``api.aggregate`` in the manager config."""

    max_scopes: int = 100
    max_group_by_fields: int = 4
    max_limit: int = 1000

    def check_scopes(self, scope_count: int) -> None:
        if scope_count > self.max_scopes:
            raise AggregateLimitExceeded(
                f"{scope_count} scopes requested; at most {self.max_scopes} are allowed"
            )

    def bounded[TRow](self, aggregator: Aggregator[TRow]) -> Aggregator[TRow]:
        """The aggregator with the limit filled in; refused when it asks for more."""
        if len(aggregator.groups) > self.max_group_by_fields:
            raise AggregateLimitExceeded(
                f"{len(aggregator.groups)} groupBy fields requested; "
                f"at most {self.max_group_by_fields} are allowed"
            )
        if aggregator.limit is None:
            return replace(aggregator, limit=self.max_limit)
        if aggregator.limit > self.max_limit:
            raise AggregateLimitExceeded(
                f"limit {aggregator.limit} requested; at most {self.max_limit} is allowed"
            )
        return aggregator
