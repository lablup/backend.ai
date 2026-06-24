import uuid

from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.models.query_types import QueryCondition
from ai.backend.manager.models.routing.conditions import RouteConditions


def _compile(condition: QueryCondition) -> str:
    return str(condition())


def test_by_replica_group_ids_generates_in_clause() -> None:
    group_ids = [ReplicaGroupID(uuid.uuid4()), ReplicaGroupID(uuid.uuid4())]
    sql = _compile(RouteConditions.by_replica_group_ids(group_ids))

    assert "routings.replica_group_id IN" in sql


def test_orphan_group_generates_is_null_clause() -> None:
    sql = _compile(RouteConditions.orphan_group())

    assert "routings.replica_group_id IS NULL" in sql
