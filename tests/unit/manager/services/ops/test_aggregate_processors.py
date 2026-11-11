"""The two aggregate processors as the registry wires them, over a mocked repository.

- A scope the caller is denied fails alone; the others are answered.
- Targets naming the same scope are checked once and answered together.
- A request over the configured limits is refused; a request with no limit gets the maximum.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Self, override
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.validator.base import PartialBulkActionValidator
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.actions.v2.ops.aggregate import AggregateLimits
from ai.backend.manager.actions.v2.ops.base import (
    GlobalAggregateOpsAction,
    PartialBulkScopedAggregateOpsAction,
)
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.errors.api import AggregateLimitExceeded
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import AggregateScopeTarget, ExistenceCheck
from ai.backend.manager.models.specs.aggregate.aggregator import (
    AggregateResult,
    AggregateValue,
    Aggregator,
)
from ai.backend.manager.models.specs.aggregate.group import GroupBy, UUIDGroupBy

_TABLE = sa.table("items", sa.column("id"))


class _OwnerID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()


@dataclass(frozen=True)
class _Target(AggregateScopeTarget):
    owner: _OwnerID
    path: str = "own"

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.owner

    @override
    def to_condition(self) -> QueryCondition:
        return lambda: sa.true()

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()

    @override
    def scope_row_ids(self) -> sa.SelectBase:
        return sa.select(_TABLE.c.id)


@dataclass
class _Aggregator(Aggregator[Any]):
    @override
    def row_class(self) -> type[Any]:
        return object

    @override
    def row_id_column(self) -> InstrumentedAttribute[Any]:
        return MagicMock()


@dataclass
class _ScopedAggregateAction(PartialBulkScopedAggregateOpsAction[Any, _Target]):
    named: Sequence[_Target]
    aggregator: _Aggregator = field(default_factory=_Aggregator)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "aggregate_test_items"

    @override
    def targets(self) -> Sequence[_Target]:
        return self.named

    @override
    def to_aggregator(self) -> _Aggregator:
        return self.aggregator

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, named=[t for t in self.named if t.scope_id() in allowed])


@dataclass
class _GlobalAggregateAction(GlobalAggregateOpsAction[Any]):
    aggregator: _Aggregator = field(default_factory=_Aggregator)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "aggregate_test_items_in_global"

    @override
    def to_aggregator(self) -> _Aggregator:
        return self.aggregator


class _AllowGlobal(GlobalActionValidator):
    @override
    async def validate(self, action: BaseGlobalAction, meta: ActionTriggerMeta) -> None:
        return None


class _DenyOwners(PartialBulkActionValidator):
    _denied: frozenset[EntityIdentifier]

    def __init__(self, denied: Sequence[EntityIdentifier]) -> None:
        self._denied = frozenset(denied)

    @override
    async def validate(self, meta: BulkActionTriggerMeta) -> Mapping[EntityIdentifier, Exception]:
        return {
            entity_id: NotEnoughPermission("denied")
            for entity_id in meta.entity_ids
            if entity_id in self._denied
        }


def _result(count: int) -> AggregateResult:
    return AggregateResult(total=AggregateValue(count=count), groups=[])


def _uuid_group() -> GroupBy:
    return UUIDGroupBy(_TABLE.c.id, with_null=False)


@pytest.fixture
def owners() -> list[_OwnerID]:
    return [_OwnerID(uuid.uuid4()) for _ in range(3)]


@pytest.fixture
def repository() -> AsyncMock:
    repository = AsyncMock()
    repository.aggregate_in_scopes.side_effect = lambda targets, aggregator: [
        _result(index) for index, _ in enumerate(targets)
    ]
    repository.aggregate_in_global.return_value = _result(7)
    return repository


def _group(repository: AsyncMock, denied: Sequence[EntityIdentifier]) -> ProcessorGroup[Any]:
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(
                global_scope=[_AllowGlobal()], partial_bulk=[_DenyOwners(denied)]
            ),
            repository=repository,
            aggregate_limits=AggregateLimits(max_scopes=3, max_group_by_fields=1, max_limit=10),
        )
    ).group(GroupMeta(UserEntityType()))


class TestPartialBulkScopedAggregate:
    async def test_a_denied_scope_fails_alone(
        self, repository: AsyncMock, owners: list[_OwnerID]
    ) -> None:
        processor = _group(repository, [owners[1]]).partial_bulk_scoped_aggregate_ops(
            _ScopedAggregateAction
        )

        result = await processor.run(_ScopedAggregateAction([_Target(owner) for owner in owners]))

        assert [item.entity_id for item in result.items] == owners
        assert isinstance(result.items[1].error, NotEnoughPermission)
        queried = repository.aggregate_in_scopes.await_args.args[0]
        assert [target.owner for target in queried] == [owners[0], owners[2]]
        assert result.items[0].value is not None
        assert result.items[2].value is not None
        assert [answer.result.total.count for answer in result.items[2].value] == [1]

    async def test_targets_of_one_scope_are_answered_together(
        self, repository: AsyncMock, owners: list[_OwnerID]
    ) -> None:
        processor = _group(repository, []).partial_bulk_scoped_aggregate_ops(_ScopedAggregateAction)
        targets = [_Target(owners[0], "own"), _Target(owners[0], "triggered")]

        result = await processor.run(_ScopedAggregateAction(targets))

        assert [item.entity_id for item in result.items] == [owners[0]]
        assert result.items[0].value is not None
        assert [answer.target for answer in result.items[0].value] == targets

    async def test_too_many_scopes_are_refused_before_any_is_checked(
        self, repository: AsyncMock
    ) -> None:
        processor = _group(repository, []).partial_bulk_scoped_aggregate_ops(_ScopedAggregateAction)
        targets = [_Target(_OwnerID(uuid.uuid4())) for _ in range(4)]

        with pytest.raises(AggregateLimitExceeded):
            await processor.run(_ScopedAggregateAction(targets))
        repository.aggregate_in_scopes.assert_not_awaited()

    async def test_no_limit_gets_the_maximum(
        self, repository: AsyncMock, owners: list[_OwnerID]
    ) -> None:
        processor = _group(repository, []).partial_bulk_scoped_aggregate_ops(_ScopedAggregateAction)

        await processor.run(_ScopedAggregateAction([_Target(owners[0])]))

        assert repository.aggregate_in_scopes.await_args.args[1].limit == 10


class TestGlobalAggregate:
    async def test_returns_the_repository_result(self, repository: AsyncMock) -> None:
        processor = _group(repository, []).global_aggregate_ops(_GlobalAggregateAction)

        result = await processor.run(_GlobalAggregateAction())

        assert result.total.count == 7

    @pytest.mark.parametrize(
        "aggregator",
        [
            pytest.param(_Aggregator(groups=[_uuid_group(), _uuid_group()]), id="group-fields"),
            pytest.param(_Aggregator(limit=11), id="limit"),
        ],
    )
    async def test_over_the_limits_is_refused(
        self, repository: AsyncMock, aggregator: _Aggregator
    ) -> None:
        processor = _group(repository, []).global_aggregate_ops(_GlobalAggregateAction)

        with pytest.raises(AggregateLimitExceeded):
            await processor.run(_GlobalAggregateAction(aggregator))
        repository.aggregate_in_global.assert_not_awaited()
