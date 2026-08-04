"""Only a create's result names an entity; the other shapes are asked for nothing.

The v2 shapes take entity type and entity id off the *action* — ``entity_type()`` on
every shape, ``entity_id()`` on the single-entity and bulk ones. The scope-shaped ones are the
exception: they target a scope, so the run reports what it reached through the result,
and the ``data/`` type supplies the id by implementing ``EntityData``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntitiesOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult


@dataclass
class _PresetData(EntityData):
    id: uuid.UUID
    name: str

    @override
    def entity_id(self) -> EntityID:
        return self.id


@dataclass
class _NameKeyedData(EntityData):
    """A domain keyed on a name, which has no id column to expose."""

    name: str

    @override
    def entity_id(self) -> EntityID:
        return uuid.uuid5(uuid.NAMESPACE_OID, self.name)


@dataclass
class _PlainData:
    """A value type that never implements ``EntityData`` — get/update/purge do not need it."""

    name: str


def test_create_result_names_the_entity_its_data_reports() -> None:
    entity_id = uuid.uuid4()

    result = CreatedEntityOpsResult(data=_PresetData(id=entity_id, name="default"))

    assert result.entity_ids() == (entity_id,)


def test_create_result_satisfies_the_scope_result_contract() -> None:
    # ``create`` targets a scope, so its result runs under the scope processor.
    entity_id = uuid.uuid4()
    result: BaseScopeActionResult = CreatedEntityOpsResult(
        data=_PresetData(id=entity_id, name="default")
    )

    assert result.entity_ids() == (entity_id,)


def test_create_result_works_for_a_name_keyed_domain() -> None:
    # No ``.id`` to read: the data maps its name to an id itself.
    data = _NameKeyedData(name="default")

    result = CreatedEntityOpsResult(data=data)

    assert result.entity_ids() == (uuid.uuid5(uuid.NAMESPACE_OID, "default"),)


def test_entity_result_carries_only_its_data() -> None:
    # The single-entity shape reads the id off the action, so the result owes nothing
    # and its data type is left alone.
    data = _PlainData(name="default")

    result = EntityOpsResult(data=data)

    assert result.data is data
    assert not isinstance(result, BaseScopeActionResult)


def test_entities_result_names_every_entity_a_many_row_write_touched() -> None:
    first, second = _PresetData(id=uuid.uuid4(), name="a"), _PresetData(id=uuid.uuid4(), name="b")

    result = EntitiesOpsResult(items=[first, second])

    assert result.entity_ids() == (first.id, second.id)


def test_entities_result_names_nothing_when_the_write_matched_nothing() -> None:
    assert EntitiesOpsResult[_PresetData](items=[]).entity_ids() == ()


def test_batch_result_names_every_entity_on_the_page() -> None:
    first, second = _PresetData(id=uuid.uuid4(), name="a"), _PresetData(id=uuid.uuid4(), name="b")

    result = BatchOpsResult(
        items=[first, second],
        total_count=2,
        has_next_page=False,
        has_previous_page=False,
    )

    assert result.entity_ids() == (first.id, second.id)


def test_batch_result_names_nothing_when_the_page_is_empty() -> None:
    result = BatchOpsResult[_PresetData](
        items=[],
        total_count=0,
        has_next_page=False,
        has_previous_page=False,
    )

    assert result.entity_ids() == ()
