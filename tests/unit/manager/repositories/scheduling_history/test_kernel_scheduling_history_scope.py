"""Tests for KernelSchedulingHistorySearchScope.

The scope is the one piece of the kernel history stack with real branching: it accepts
two optional axes, must reject an empty scope, and must intersect when both are given.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import pytest

from ai.backend.manager.errors.kernel import EmptyKernelSchedulingHistoryScope
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.scheduling_history.types import (
    KernelSchedulingHistorySearchScope,
)

_SESSION_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
_KERNEL_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@dataclass(frozen=True)
class _ExistenceCheckExpectation:
    column_name: str
    value: uuid.UUID


@dataclass(frozen=True)
class _ScopeCase:
    session_id: uuid.UUID | None
    kernel_id: uuid.UUID | None
    expected_sql_fragments: list[str] = field(default_factory=list)
    expected_checks: list[_ExistenceCheckExpectation] = field(default_factory=list)


def _scope_case_id(case: _ScopeCase) -> str:
    return f"session={case.session_id is not None}-kernel={case.kernel_id is not None}"


class TestKernelSchedulingHistorySearchScope:
    """Test cases for the kernel scheduling history search scope."""

    def test_empty_scope_is_rejected(self) -> None:
        with pytest.raises(EmptyKernelSchedulingHistoryScope):
            KernelSchedulingHistorySearchScope()

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeCase(
                session_id=_SESSION_ID,
                kernel_id=None,
                expected_sql_fragments=["kernel_scheduling_history.session_id ="],
            ),
            _ScopeCase(
                session_id=None,
                kernel_id=_KERNEL_ID,
                expected_sql_fragments=["kernel_scheduling_history.kernel_id ="],
            ),
            _ScopeCase(
                session_id=_SESSION_ID,
                kernel_id=_KERNEL_ID,
                expected_sql_fragments=[
                    "kernel_scheduling_history.session_id =",
                    "kernel_scheduling_history.kernel_id =",
                ],
            ),
        ],
        ids=_scope_case_id,
    )
    def test_to_condition_filters_on_each_given_axis(self, case: _ScopeCase) -> None:
        scope = KernelSchedulingHistorySearchScope(
            session_id=case.session_id, kernel_id=case.kernel_id
        )

        rendered = str(scope.to_condition()())

        for fragment in case.expected_sql_fragments:
            assert fragment in rendered

    def test_to_condition_intersects_both_axes(self) -> None:
        scope = KernelSchedulingHistorySearchScope(session_id=_SESSION_ID, kernel_id=_KERNEL_ID)

        rendered = str(scope.to_condition()())

        assert " AND " in rendered

    @pytest.mark.parametrize(
        "case",
        [
            _ScopeCase(
                session_id=_SESSION_ID,
                kernel_id=None,
                expected_checks=[
                    _ExistenceCheckExpectation(column_name="id", value=_SESSION_ID),
                ],
            ),
            _ScopeCase(
                session_id=None,
                kernel_id=_KERNEL_ID,
                expected_checks=[
                    _ExistenceCheckExpectation(column_name="id", value=_KERNEL_ID),
                ],
            ),
            _ScopeCase(
                session_id=_SESSION_ID,
                kernel_id=_KERNEL_ID,
                expected_checks=[
                    _ExistenceCheckExpectation(column_name="id", value=_SESSION_ID),
                    _ExistenceCheckExpectation(column_name="id", value=_KERNEL_ID),
                ],
            ),
        ],
        ids=_scope_case_id,
    )
    def test_existence_checks_cover_each_given_axis(self, case: _ScopeCase) -> None:
        scope = KernelSchedulingHistorySearchScope(
            session_id=case.session_id, kernel_id=case.kernel_id
        )

        checks = scope.existence_checks

        assert [
            _ExistenceCheckExpectation(column_name=c.column.key, value=c.value) for c in checks
        ] == case.expected_checks

    def test_existence_checks_point_at_the_owning_tables(self) -> None:
        scope = KernelSchedulingHistorySearchScope(session_id=_SESSION_ID, kernel_id=_KERNEL_ID)

        checks = scope.existence_checks

        assert checks[0].column is SessionRow.id
        assert checks[1].column is KernelRow.id
