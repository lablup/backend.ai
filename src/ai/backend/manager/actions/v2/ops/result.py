"""Results shared by every ops-backed action, one per target shape.

Domains used to write a result type per operation whose only distinguishing feature was
the field name — ``allow_list=``, ``vfolder=``, ``image=`` — which is what forced a
conversion step between the repository and the result. These replace all of them.

There are six rather than one because the v2 shapes ask different things of a result.
A single-entity run is identified by its action, so its result owes nothing; a run over
a scope has to name what it touched and a lookup has to produce the id it resolved,
neither of which the action can know; those get it from the ``data/`` type, which says
so by implementing :class:`EntityData`. The bulk shape is different again — the caller
named the entities, so it answers for each one against that list.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.bulk.result import BaseBulkActionResult, BulkEntityResult
from ai.backend.manager.actions.v2.lookup.base import BaseLookupActionResult
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult

__all__ = (
    "EntityOpsResult",
    "CreatedEntityOpsResult",
    "LookupOpsResult",
    "EntitiesOpsResult",
    "BulkOpsResult",
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
class BulkOpsResult[TData](BaseBulkActionResult):
    """How each entity a bulk write named fared.

    The bulk shape is the one that reports per entity: the caller named them, so each
    one's fate is answered against that expectation rather than the run carrying a
    single verdict. A partial success says SUCCESS for what went through and ERROR for
    the rest.

    Needs no :class:`EntityData`, unlike the scope and lookup results: the ids are the
    ones the caller passed in, not something to recover from what came back.
    """

    successes: dict[EntityID, TData]
    errors: dict[EntityID, Exception]

    @override
    def entity_results(self) -> Sequence[BulkEntityResult]:
        """Successes first, then errors — not the caller's order.

        Classification is :class:`ActionRunStatus`'s, the same one the processors use to
        turn a raised exception into audit-visible fields, so a bulk entity's error
        reads exactly like a single run's.
        """
        success_status = ActionRunStatus.success()
        results = [
            BulkEntityResult(
                entity_id=entity_id,
                status=success_status.status,
                description=success_status.description,
                error_code=success_status.error_code,
            )
            for entity_id in self.successes
        ]
        for entity_id, exception in self.errors.items():
            failure = ActionRunStatus.of_failure(exception, during_validation=False)
            results.append(
                BulkEntityResult(
                    entity_id=entity_id,
                    status=failure.status,
                    description=failure.description,
                    error_code=failure.error_code,
                )
            )
        return results


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
