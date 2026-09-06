from dataclasses import dataclass, field

from ai.backend.manager.actions.v2.bulk.validator.base import (
    AtomicBulkActionValidator,
    PartialBulkActionValidator,
)
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.actions.v2.lookup.validator.base import LookupActionValidator
from ai.backend.manager.actions.v2.relation.validator.base import RelationActionValidator
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.single_entity.validator.base import SingleEntityActionValidator

__all__ = ("ActionValidators",)


@dataclass
class ActionValidators:
    """Validators per target shape, mirroring :class:`ActionMonitors`."""

    single_entity: list[SingleEntityActionValidator] = field(default_factory=list)
    partial_bulk: list[PartialBulkActionValidator] = field(default_factory=list)
    atomic_bulk: list[AtomicBulkActionValidator] = field(default_factory=list)
    scope: list[ScopeActionValidator] = field(default_factory=list)
    relation: list[RelationActionValidator] = field(default_factory=list)
    global_scope: list[GlobalActionValidator] = field(default_factory=list)
    lookup: list[LookupActionValidator] = field(default_factory=list)
