from dataclasses import dataclass, field

from ai.backend.manager.actions.v2.bulk.validator.base import (
    AtomicBulkActionValidator,
    PartialBulkActionValidator,
)
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.actions.v2.lookup.validator.base import LookupActionValidator
from ai.backend.manager.actions.v2.membership.validator.base import MembershipActionValidator
from ai.backend.manager.actions.v2.relation.validator.base import RelationActionValidator
from ai.backend.manager.actions.v2.scope.validator.base import ScopeActionValidator
from ai.backend.manager.actions.v2.single_entity.validator.base import SingleEntityActionValidator

__all__ = ("ActionValidators",)


@dataclass
class ActionValidators:
    """Validators per target shape, mirroring :class:`ActionMonitors`.

    ``global_scope`` is stated rather than defaulted: an empty list there is what a
    global processor refuses to be built with, so handing one out by default would put
    the refusal at every wiring instead of at the one that forgot the gate.
    """

    global_scope: list[GlobalActionValidator]
    single_entity: list[SingleEntityActionValidator] = field(default_factory=list)
    partial_bulk: list[PartialBulkActionValidator] = field(default_factory=list)
    atomic_bulk: list[AtomicBulkActionValidator] = field(default_factory=list)
    scope: list[ScopeActionValidator] = field(default_factory=list)
    relation: list[RelationActionValidator] = field(default_factory=list)
    membership: list[MembershipActionValidator] = field(default_factory=list)
    lookup: list[LookupActionValidator] = field(default_factory=list)
