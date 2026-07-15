from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.common.data.filter_specs import StringInMatchSpec, StringMatchSpec
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scheduling_history.conditions import (
    KernelSchedulingHistoryConditions,
)


@dataclass(frozen=True)
class _ConditionCase:
    label: str
    condition: QueryCondition
    expected_sql: str


class TestKernelSchedulingHistoryConditions:
    @pytest.mark.parametrize(
        "case",
        [
            _ConditionCase(
                label="by_from_status",
                condition=KernelSchedulingHistoryConditions.by_from_status(
                    KernelSchedulingPhase.PULLING
                ),
                expected_sql="kernel_scheduling_history.from_status = 'PULLING'",
            ),
            _ConditionCase(
                label="by_to_status",
                condition=KernelSchedulingHistoryConditions.by_to_status(
                    KernelSchedulingPhase.RUNNING
                ),
                expected_sql="kernel_scheduling_history.to_status = 'RUNNING'",
            ),
            _ConditionCase(
                label="by_phase_contains",
                condition=KernelSchedulingHistoryConditions.by_phase_contains(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=False)
                ),
                expected_sql="kernel_scheduling_history.phase LIKE '%PULLING%'",
            ),
            _ConditionCase(
                label="by_phase_contains-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_contains(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=True)
                ),
                expected_sql="kernel_scheduling_history.phase NOT LIKE '%PULLING%'",
            ),
            _ConditionCase(
                label="by_phase_contains-case_insensitive",
                condition=KernelSchedulingHistoryConditions.by_phase_contains(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=False)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) LIKE '%pulling%'",
            ),
            _ConditionCase(
                label="by_phase_contains-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_contains(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=True)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) NOT LIKE '%pulling%'",
            ),
            _ConditionCase(
                label="by_phase_equals",
                condition=KernelSchedulingHistoryConditions.by_phase_equals(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=False)
                ),
                expected_sql="kernel_scheduling_history.phase = 'PULLING'",
            ),
            _ConditionCase(
                label="by_phase_equals-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_equals(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=True)
                ),
                expected_sql="kernel_scheduling_history.phase != 'PULLING'",
            ),
            _ConditionCase(
                label="by_phase_equals-case_insensitive",
                condition=KernelSchedulingHistoryConditions.by_phase_equals(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=False)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) = 'pulling'",
            ),
            _ConditionCase(
                label="by_phase_equals-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_equals(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=True)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) != 'pulling'",
            ),
            _ConditionCase(
                label="by_phase_starts_with",
                condition=KernelSchedulingHistoryConditions.by_phase_starts_with(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=False)
                ),
                expected_sql="kernel_scheduling_history.phase LIKE 'PULLING%'",
            ),
            _ConditionCase(
                label="by_phase_starts_with-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_starts_with(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=True)
                ),
                expected_sql="kernel_scheduling_history.phase NOT LIKE 'PULLING%'",
            ),
            _ConditionCase(
                label="by_phase_starts_with-case_insensitive",
                condition=KernelSchedulingHistoryConditions.by_phase_starts_with(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=False)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) LIKE 'pulling%'",
            ),
            _ConditionCase(
                label="by_phase_starts_with-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_starts_with(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=True)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) NOT LIKE 'pulling%'",
            ),
            _ConditionCase(
                label="by_phase_ends_with",
                condition=KernelSchedulingHistoryConditions.by_phase_ends_with(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=False)
                ),
                expected_sql="kernel_scheduling_history.phase LIKE '%PULLING'",
            ),
            _ConditionCase(
                label="by_phase_ends_with-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_ends_with(
                    StringMatchSpec(value="PULLING", case_insensitive=False, negated=True)
                ),
                expected_sql="kernel_scheduling_history.phase NOT LIKE '%PULLING'",
            ),
            _ConditionCase(
                label="by_phase_ends_with-case_insensitive",
                condition=KernelSchedulingHistoryConditions.by_phase_ends_with(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=False)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) LIKE '%pulling'",
            ),
            _ConditionCase(
                label="by_phase_ends_with-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_ends_with(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=True)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) NOT LIKE '%pulling'",
            ),
            _ConditionCase(
                label="by_phase_in",
                condition=KernelSchedulingHistoryConditions.by_phase_in(
                    StringInMatchSpec(
                        values=["PULLING", "CREATING"], case_insensitive=False, negated=False
                    )
                ),
                expected_sql="kernel_scheduling_history.phase IN ('PULLING', 'CREATING')",
            ),
            _ConditionCase(
                label="by_phase_in-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_in(
                    StringInMatchSpec(
                        values=["PULLING", "CREATING"], case_insensitive=False, negated=True
                    )
                ),
                expected_sql="(kernel_scheduling_history.phase NOT IN ('PULLING', 'CREATING'))",
            ),
            _ConditionCase(
                label="by_phase_in-case_insensitive",
                condition=KernelSchedulingHistoryConditions.by_phase_in(
                    StringInMatchSpec(
                        values=["PULLING", "CREATING"], case_insensitive=True, negated=False
                    )
                ),
                expected_sql="lower(kernel_scheduling_history.phase) IN ('pulling', 'creating')",
            ),
            _ConditionCase(
                label="by_phase_in-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_in(
                    StringInMatchSpec(
                        values=["PULLING", "CREATING"], case_insensitive=True, negated=True
                    )
                ),
                expected_sql=(
                    "(lower(kernel_scheduling_history.phase) NOT IN ('pulling', 'creating'))"
                ),
            ),
        ],
        ids=lambda case: case.label,
    )
    def test_condition_compiles_to_expected_sql(self, case: _ConditionCase) -> None:
        sql = str(case.condition().compile(compile_kwargs={"literal_binds": True}))

        assert sql == case.expected_sql
