"""Tests for ``BulkActionProcessor``: validator chain + all-or-nothing denial.

Any denial across the full validator chain raises ``PermissionDeniedError``
after every validator has run, aggregating all denied refs into the error.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import override

import pytest

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.exception import PermissionDeniedError
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.processor.bulk import (
    BulkActionProcessor,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.validator.bulk import (
    BulkActionValidator,
    BulkValidationResult,
    DeniedEntity,
)
from ai.backend.manager.data.permission.types import RBACElementRef


@pytest.fixture
def ref_a() -> RBACElementRef:
    return RBACElementRef(element_type=RBACElementType.SESSION, element_id="a")


@pytest.fixture
def ref_b() -> RBACElementRef:
    return RBACElementRef(element_type=RBACElementType.SESSION, element_id="b")


@pytest.fixture
def ref_c() -> RBACElementRef:
    return RBACElementRef(element_type=RBACElementType.SESSION, element_id="c")


@dataclass
class _MockBulkAction(BaseBulkAction):
    refs: list[RBACElementRef]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.refs)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class _MockBulkActionResult(BaseBulkActionResult):
    processed_refs: list[RBACElementRef] = field(default_factory=list)

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.processed_refs)


class _AllowSetValidator(BulkActionValidator):
    """Approves any ref in ``allowed``; anything else visible is denied."""

    def __init__(self, allowed: set[RBACElementRef]) -> None:
        self._allowed = set(allowed)

    @classmethod
    @override
    def name(cls) -> str:
        return "allow-set"

    @override
    async def validate(
        self, action: BaseBulkAction, meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        current = list(action.element_refs())
        allowed = [r for r in current if r in self._allowed]
        denied = [
            DeniedEntity(entity_ref=r, deny_reason="not in allow-set")
            for r in current
            if r not in self._allowed
        ]
        return BulkValidationResult(allowed_entities=allowed, denied_entities=denied)


class _RecordingValidator(BulkActionValidator):
    """Captures the refs each ``validate()`` call received."""

    def __init__(self, allowed: set[RBACElementRef]) -> None:
        self._allowed = set(allowed)
        self.observed_batches: list[list[RBACElementRef]] = []

    @classmethod
    @override
    def name(cls) -> str:
        return "recording"

    @override
    async def validate(
        self, action: BaseBulkAction, meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        current = list(action.element_refs())
        self.observed_batches.append(current)
        allowed = [r for r in current if r in self._allowed]
        denied = [
            DeniedEntity(entity_ref=r, deny_reason="blocked")
            for r in current
            if r not in self._allowed
        ]
        return BulkValidationResult(allowed_entities=allowed, denied_entities=denied)


def _echo_func() -> Callable[[_MockBulkAction], Awaitable[_MockBulkActionResult]]:
    async def _run(action: _MockBulkAction) -> _MockBulkActionResult:
        return _MockBulkActionResult(processed_refs=list(action.element_refs()))

    return _run


class TestBulkActionProcessor:
    async def test_no_validators_passes_all_refs_through(
        self,
        ref_a: RBACElementRef,
        ref_b: RBACElementRef,
        ref_c: RBACElementRef,
    ) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
        )
        action = _MockBulkAction(refs=[ref_a, ref_b, ref_c])

        result = await processor.wait_for_complete(action)

        assert result.processed_refs == [ref_a, ref_b, ref_c]

    async def test_all_allowed_runs_action_normally(
        self,
        ref_a: RBACElementRef,
        ref_b: RBACElementRef,
        ref_c: RBACElementRef,
    ) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={ref_a, ref_b, ref_c})],
        )
        action = _MockBulkAction(refs=[ref_a, ref_b, ref_c])

        result = await processor.wait_for_complete(action)

        assert result.processed_refs == [ref_a, ref_b, ref_c]

    async def test_single_validator_partial_denial_raises(
        self,
        ref_a: RBACElementRef,
        ref_b: RBACElementRef,
        ref_c: RBACElementRef,
    ) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={ref_a, ref_c})],
        )
        action = _MockBulkAction(refs=[ref_a, ref_b, ref_c])

        with pytest.raises(PermissionDeniedError) as exc_info:
            await processor.wait_for_complete(action)

        msg = str(exc_info.value)
        assert ref_b.to_str() in msg
        assert "not in allow-set" in msg

    async def test_full_chain_runs_before_raising(
        self,
        ref_a: RBACElementRef,
        ref_b: RBACElementRef,
        ref_c: RBACElementRef,
    ) -> None:
        """Every validator runs even when an earlier one denied refs."""
        first = _RecordingValidator(allowed={ref_a, ref_b})
        second = _RecordingValidator(allowed={ref_a})
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[first, second],
        )
        action = _MockBulkAction(refs=[ref_a, ref_b, ref_c])

        with pytest.raises(PermissionDeniedError) as exc_info:
            await processor.wait_for_complete(action)

        # Both validators saw the original (unfiltered) action.
        assert first.observed_batches == [[ref_a, ref_b, ref_c]]
        assert second.observed_batches == [[ref_a, ref_b, ref_c]]
        # Aggregated denials from both validators surface in the error,
        # each paired with its deny reason.
        msg = str(exc_info.value)
        assert f"{ref_b.to_str()} (blocked)" in msg
        assert f"{ref_c.to_str()} (blocked)" in msg

    async def test_original_action_is_not_mutated(
        self,
        ref_a: RBACElementRef,
        ref_b: RBACElementRef,
    ) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={ref_a, ref_b})],
        )
        original = _MockBulkAction(refs=[ref_a, ref_b])

        await processor.wait_for_complete(original)

        assert original.element_refs() == [ref_a, ref_b]
