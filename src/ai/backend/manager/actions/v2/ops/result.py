"""Results shared by every ops-backed action, one per target shape.

Domains used to write a result type per operation whose only distinguishing feature was
the field name — ``allow_list=``, ``vfolder=``, ``image=`` — which is what forced a
conversion step between the repository and the result. These replace all of them.

There are seven rather than one because the v2 shapes ask different things of a result.
A single-entity run is identified by its action, so its result owes nothing; a run over
a scope has to name what it touched and a lookup has to produce the id it resolved,
neither of which the action can know; those get it from the ``data/`` type, which says
so by implementing :class:`EntityData`. The bulk shape is different again — the caller
named the entities, so it answers for each one against that list.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import (
    EntityData,
    EntityIdentifier,
    FieldData,
    FieldIdentifier,
)
from ai.backend.manager.actions.run_status import ActionRunStatus
from ai.backend.manager.actions.v2.bulk.result import BasePartialBulkActionResult, BulkEntityResult
from ai.backend.manager.actions.v2.lookup.base import BaseLookupActionResult
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult

__all__ = (
    "EntityOpsResult",
    "CreatedEntityOpsResult",
    "CreatedEntityWithFieldsOpsResult",
    "LookupOpsResult",
    "CreatedFieldOpsResult",
    "FieldsOpsResult",
    "BulkFieldOpsResult",
    "FieldOwnerLookupOpsResult",
    "EntitiesOpsResult",
    "BulkOpsResult",
    "BatchOpsResult",
    "ScopedBatchOpsResult",
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
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.data.entity_id(),)


@dataclass
class CreatedEntityWithFieldsOpsResult[TData: EntityData, TFieldData](
    CreatedEntityOpsResult[TData]
):
    """The entity a create produced, and the field rows created under it.

    Reports the entity alone as what was touched: the field rows are owned by it
    and carry no independent identity for the audit trail to name.
    """

    fields: list[TFieldData]


@dataclass
class LookupOpsResult[TEntityID: EntityIdentifier](BaseLookupActionResult):
    """The id of the entity a lookup's key names.

    A lookup declares no target — producing one is the point of the run — so the id
    reaches the audit trail through the result, the same way a create's does.

    Carries the id alone: what the caller does next is an operation on that entity, and
    the value behind the id is read by a get, which says for itself what to load.
    """

    resolved_entity_id: TEntityID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.resolved_entity_id


@dataclass
class FieldOwnerLookupOpsResult(BaseLookupActionResult):
    """The id of the entity a field row belongs to.

    Carries the id alone: the owner's data is never read, because this value exists to
    name the RBAC target and the audit row of the operation that follows.
    """

    owner_entity_id: EntityIdentifier

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.owner_entity_id


@dataclass
class BulkOpsResult[TData](BasePartialBulkActionResult):
    """How each entity a bulk write named fared.

    The bulk shape is the one that reports per entity: the caller named them, so each
    one's fate is answered against that expectation rather than the run carrying a
    single verdict. A partial success says SUCCESS for what went through and ERROR for
    the rest.

    Needs no :class:`EntityData`, unlike the scope and lookup results: the ids are the
    ones the caller passed in, not something to recover from what came back.
    """

    successes: dict[EntityIdentifier, TData]
    errors: dict[EntityIdentifier, Exception]

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
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(item.entity_id() for item in self.items)


@dataclass
class BulkFieldOpsResult[TData]:
    """How each field row a bulk write named fared.

    Keyed by the field rows the caller named, unlike :class:`BulkOpsResult`: the answer
    the caller expects is per row. What the run is recorded against is the entity owning
    each row, which the processor resolves.
    """

    successes: dict[FieldIdentifier, TData]
    errors: dict[FieldIdentifier, Exception]


@dataclass
class CreatedFieldOpsResult[TData: FieldData](EntityOpsResult[TData]):
    """The field row a write created."""


@dataclass
class FieldsOpsResult[TData: FieldData]:
    """Every field row a write created.

    Names nothing on its own: the operation is answered for by the owner the action
    already declares, so there is no id for this result to report.
    """

    items: list[TData]


@dataclass
class BatchOpsResult[TData]:
    """A page of entities.

    Mirrors the fields of ``SearcherResult`` so the repository result carries straight
    through. Carries no contract, which is what a global search needs: that shape is
    gated on the SUPERADMIN role and reports no target.
    """

    items: list[TData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class ScopedFieldsOpsResult[TData](BatchOpsResult[TData], BaseScopeActionResult):
    """A page of the field rows read within one owner's scope.

    Names no entity: a field row is not one, so there is no id to report. Which owner
    the read stayed inside is on the action's scope targets, which the audit row is
    tied to. Unlike the entity page, the data type is therefore unconstrained.
    """

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


@dataclass
class ScopedBatchOpsResult[TData: EntityData](BatchOpsResult[TData], BaseScopeActionResult):
    """A page of entities read within a scope.

    Separate from the global page because only this one is asked what it reached, and
    only this one therefore needs its ``data/`` type to implement :class:`EntityData`.
    """

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        """Every entity on the page.

        A read still names what it reached. How much of that is worth recording is the
        audit policy's call — reads are the configurable half of it — not something to
        settle by returning less than the run knows.
        """
        return tuple(item.entity_id() for item in self.items)
