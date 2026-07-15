from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Dialect

from ai.backend.common.data.filter_specs import (
    StringInMatchSpec,
    StringMatchSpec,
    UUIDEqualMatchSpec,
)
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scheduling_history.conditions import (
    KernelSchedulingHistoryConditions,
)

_KERNEL_ID = KernelId(uuid.UUID("11111111-1111-1111-1111-111111111111"))
_SESSION_ID = SessionId(uuid.UUID("22222222-2222-2222-2222-222222222222"))

# postgresql.dialect (PGDialect) has untyped __init__; assign via Any to avoid [no-untyped-call].
_pg_dialect_cls: Any = postgresql.dialect
_PG_DIALECT: Dialect = _pg_dialect_cls()


@dataclass(frozen=True)
class _ConditionCase:
    label: str
    condition: QueryCondition
    expected_sql: str
    # GUID falls back to CHAR(16) on the default dialect, which has no literal
    # processor, so UUID columns only render inline under postgresql.
    dialect: Dialect | None = None


class TestKernelSchedulingHistoryConditions:
    @pytest.mark.parametrize(
        "case",
        [
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
                expected_sql="lower(kernel_scheduling_history.phase) LIKE lower('%PULLING%')",
            ),
            _ConditionCase(
                label="by_phase_contains-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_contains(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=True)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) NOT LIKE lower('%PULLING%')",
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
                expected_sql="lower(kernel_scheduling_history.phase) LIKE lower('PULLING%')",
            ),
            _ConditionCase(
                label="by_phase_starts_with-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_starts_with(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=True)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) NOT LIKE lower('PULLING%')",
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
                expected_sql="lower(kernel_scheduling_history.phase) LIKE lower('%PULLING')",
            ),
            _ConditionCase(
                label="by_phase_ends_with-case_insensitive-negated",
                condition=KernelSchedulingHistoryConditions.by_phase_ends_with(
                    StringMatchSpec(value="PULLING", case_insensitive=True, negated=True)
                ),
                expected_sql="lower(kernel_scheduling_history.phase) NOT LIKE lower('%PULLING')",
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
            _ConditionCase(
                label="by_from_statuses",
                condition=KernelSchedulingHistoryConditions.by_from_statuses([
                    "PULLING",
                    "CREATING",
                ]),
                expected_sql="kernel_scheduling_history.from_status IN ('PULLING', 'CREATING')",
            ),
            _ConditionCase(
                label="by_to_statuses",
                condition=KernelSchedulingHistoryConditions.by_to_statuses(["RUNNING"]),
                expected_sql="kernel_scheduling_history.to_status IN ('RUNNING')",
            ),
            _ConditionCase(
                label="by_result",
                condition=KernelSchedulingHistoryConditions.by_result(SchedulingResult.SUCCESS),
                expected_sql="kernel_scheduling_history.result = 'SUCCESS'",
            ),
            _ConditionCase(
                label="by_error_code_equals",
                condition=KernelSchedulingHistoryConditions.by_error_code_equals(
                    StringMatchSpec(value="ERR", case_insensitive=False, negated=False)
                ),
                expected_sql="kernel_scheduling_history.error_code = 'ERR'",
            ),
            _ConditionCase(
                label="by_kernel_id",
                condition=KernelSchedulingHistoryConditions.by_kernel_id(_KERNEL_ID),
                expected_sql=(
                    "kernel_scheduling_history.kernel_id = '11111111-1111-1111-1111-111111111111'"
                ),
                dialect=_PG_DIALECT,
            ),
            _ConditionCase(
                label="by_session_id",
                condition=KernelSchedulingHistoryConditions.by_session_id(_SESSION_ID),
                expected_sql=(
                    "kernel_scheduling_history.session_id = '22222222-2222-2222-2222-222222222222'"
                ),
                dialect=_PG_DIALECT,
            ),
            _ConditionCase(
                label="by_kernel_id_filter",
                condition=KernelSchedulingHistoryConditions.by_kernel_id_filter(
                    UUIDEqualMatchSpec(value=_KERNEL_ID, negated=False)
                ),
                expected_sql=(
                    "kernel_scheduling_history.kernel_id = '11111111-1111-1111-1111-111111111111'"
                ),
                dialect=_PG_DIALECT,
            ),
            _ConditionCase(
                label="by_kernel_id_filter-negated",
                condition=KernelSchedulingHistoryConditions.by_kernel_id_filter(
                    UUIDEqualMatchSpec(value=_KERNEL_ID, negated=True)
                ),
                expected_sql=(
                    "kernel_scheduling_history.kernel_id != '11111111-1111-1111-1111-111111111111'"
                ),
                dialect=_PG_DIALECT,
            ),
            _ConditionCase(
                label="by_session_id_filter",
                condition=KernelSchedulingHistoryConditions.by_session_id_filter(
                    UUIDEqualMatchSpec(value=_SESSION_ID, negated=False)
                ),
                expected_sql=(
                    "kernel_scheduling_history.session_id = '22222222-2222-2222-2222-222222222222'"
                ),
                dialect=_PG_DIALECT,
            ),
        ],
        ids=lambda case: case.label,
    )
    def test_condition_compiles_to_expected_sql(self, case: _ConditionCase) -> None:
        sql = str(
            case.condition().compile(dialect=case.dialect, compile_kwargs={"literal_binds": True})
        )

        assert sql == case.expected_sql
