"""Results shared by every ops-backed action, one per target shape.

Domains used to write a result type per operation whose only distinguishing feature was
the field name — ``allow_list=``, ``vfolder=``, ``image=`` — which is what forced a
conversion step between the repository and the result. These replace all of them.

There are five rather than one because the v2 shapes ask different things of a result.
A single-entity run is identified by its action, so its result owes nothing; a run over
a scope has to name what it touched and a lookup has to produce the id it resolved,
neither of which the action can know. Those results get it from the ``data/`` type,
which says so by implementing :class:`EntityData`.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.v2.lookup.base import BaseLookupActionResult
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult

__all__ = (
    "EntityOpsResult",
    "CreatedEntityOpsResult",
    "LookupOpsResult",
    "EntitiesOpsResult",
    "BatchOpsResult",
)


@dataclass
class EntityOpsResult[TData]:
    """One entity, from a run that already named it.

    Carries no contract because the single-entity shape asks for none: the processor
    reads the id off ``BaseSingleEntityAction.entity_id()``, not off the result.
    """

    data: TData


@dataclass
class CreatedEntityOpsResult[TData: EntityData](EntityOpsResult[TData], BaseScopeActionResult):
    """The entity a create produced.

    A create targets a scope rather than an entity, so the shape reports what was
    touched through the result, and nothing upstream knows the id until the row exists.
    The value that came back is the only thing that does, which is why ``TData`` is
    bounded by :class:`EntityData` here and nowhere else.
    """

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return (self.data.entity_id(),)


@dataclass
class LookupOpsResult[TData: EntityData](EntityOpsResult[TData], BaseLookupActionResult):
    """The entity a lookup resolved its key to.

    A lookup declares no target — producing one is the point of the run — so the id
    reaches the audit trail through the result, the same way a create's does.
    """

    @override
    def resolved_entity_id(self) -> EntityID:
        return self.data.entity_id()


@dataclass
class EntitiesOpsResult[TData: EntityData](BaseScopeActionResult):
    """Every entity a scope-shaped write touched.

    Result of the many-row writes — a bulk create, or a batch update or purge over a
    scope. Unlike :class:`BatchOpsResult` it carries no page: the caller named a
    condition, not a window, so there is nothing to page through.
    """

    items: list[TData]

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return tuple(item.entity_id() for item in self.items)


@dataclass
class BatchOpsResult[TData: EntityData](BaseScopeActionResult):
    """A page of entities, from a search over a scope.

    Mirrors the fields of ``SearcherResult`` so the repository result carries straight
    through.
    """

    items: list[TData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        """Every entity on the page.

        A read still names what it reached. How much of that is worth recording is the
        audit policy's call — reads are the configurable half of it — not something to
        settle by returning less than the run knows.
        """
        return tuple(item.entity_id() for item in self.items)
