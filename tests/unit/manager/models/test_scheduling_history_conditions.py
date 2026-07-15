import uuid
from dataclasses import dataclass

import pytest

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scheduling_history.conditions import (
    KernelSchedulingHistoryConditions,
)


def _compile(condition: QueryCondition) -> str:
    return str(condition())


@dataclass(frozen=True)
class _ConditionCase:
    condition: QueryCondition
    expected_sql: str


@pytest.mark.parametrize(
    "case",
    [
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_from_status(
                KernelSchedulingPhase.PREPARING
            ),
            expected_sql="kernel_scheduling_history.from_status =",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_to_status(KernelSchedulingPhase.RUNNING),
            expected_sql="kernel_scheduling_history.to_status =",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_from_statuses(["PREPARING", "PULLING"]),
            expected_sql="kernel_scheduling_history.from_status IN",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_to_statuses(["RUNNING"]),
            expected_sql="kernel_scheduling_history.to_status IN",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_kernel_id(KernelId(uuid.uuid4())),
            expected_sql="kernel_scheduling_history.kernel_id =",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_session_id(SessionId(uuid.uuid4())),
            expected_sql="kernel_scheduling_history.session_id =",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_kernel_id_filter(
                UUIDEqualMatchSpec(value=uuid.uuid4(), negated=False)
            ),
            expected_sql="kernel_scheduling_history.kernel_id =",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_session_id_filter(
                UUIDEqualMatchSpec(value=uuid.uuid4(), negated=False)
            ),
            expected_sql="kernel_scheduling_history.session_id =",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_result(SchedulingResult.SUCCESS),
            expected_sql="kernel_scheduling_history.result =",
        ),
        _ConditionCase(
            condition=KernelSchedulingHistoryConditions.by_error_code("ERR"),
            expected_sql="kernel_scheduling_history.error_code =",
        ),
    ],
    ids=lambda case: case.expected_sql.replace("kernel_scheduling_history.", "").replace(" ", "_"),
)
def test_conditions_compile_against_the_real_columns(case: _ConditionCase) -> None:
    # Each factory builds a lazy closure, so a bad column name only surfaces here.
    assert case.expected_sql in _compile(case.condition)
