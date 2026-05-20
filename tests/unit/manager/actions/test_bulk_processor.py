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


def _ref(element_type: RBACElementType, element_id: str) -> RBACElementRef:
    return RBACElementRef(element_type=element_type, element_id=element_id)


_REF_A = _ref(RBACElementType.SESSION, "a")
_REF_B = _ref(RBACElementType.SESSION, "b")
_REF_C = _ref(RBACElementType.SESSION, "c")


@dataclass
class _MockBulkAction(BaseBulkAction):
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
        current = list(action.element_refs)
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
        current = list(action.element_refs)
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
        return _MockBulkActionResult(processed_refs=list(action.element_refs))

    return _run


class TestBulkActionProcessor:
    async def test_no_validators_passes_all_refs_through(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
        )
        action = _MockBulkAction(element_refs=[_REF_A, _REF_B, _REF_C])

        outcome = await processor.wait_for_complete(action)

        assert outcome.result.processed_refs == [_REF_A, _REF_B, _REF_C]
        assert outcome.validator_decisions == []

    async def test_all_allowed_runs_action_normally(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={_REF_A, _REF_B, _REF_C})],
        )
        action = _MockBulkAction(element_refs=[_REF_A, _REF_B, _REF_C])

        outcome = await processor.wait_for_complete(action)

        assert outcome.result.processed_refs == [_REF_A, _REF_B, _REF_C]
        decision = outcome.validator_decisions[0]
        assert decision.results.allowed_entities == [_REF_A, _REF_B, _REF_C]
        assert decision.results.denied_entities == []

    async def test_single_validator_partial_denial_raises(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={_REF_A, _REF_C})],
        )
        action = _MockBulkAction(element_refs=[_REF_A, _REF_B, _REF_C])

        with pytest.raises(PermissionDeniedError) as exc_info:
            await processor.wait_for_complete(action)

        msg = str(exc_info.value)
        assert _REF_B.to_str() in msg
        assert "not in allow-set" in msg

    async def test_full_chain_runs_before_raising(self) -> None:
        """Every validator runs even when an earlier one denied refs."""
        first = _RecordingValidator(allowed={_REF_A, _REF_B})
        second = _RecordingValidator(allowed={_REF_A})
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[first, second],
        )
        action = _MockBulkAction(element_refs=[_REF_A, _REF_B, _REF_C])

        with pytest.raises(PermissionDeniedError) as exc_info:
            await processor.wait_for_complete(action)

        # Both validators saw the original (unfiltered) action.
        assert first.observed_batches == [[_REF_A, _REF_B, _REF_C]]
        assert second.observed_batches == [[_REF_A, _REF_B, _REF_C]]
        # Aggregated denials from both validators surface in the error,
        # each paired with its deny reason.
        msg = str(exc_info.value)
        assert f"{_REF_B.to_str()} (blocked)" in msg
        assert f"{_REF_C.to_str()} (blocked)" in msg

    async def test_original_action_is_not_mutated(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={_REF_A, _REF_B})],
        )
        original = _MockBulkAction(element_refs=[_REF_A, _REF_B])

        await processor.wait_for_complete(original)

        assert original.element_refs == [_REF_A, _REF_B]


@pytest.mark.parametrize(
    ("allowed", "batch", "expected_processed"),
    [
        ({_REF_A, _REF_B}, [_REF_A, _REF_B], [_REF_A, _REF_B]),
    ],
)
async def test_full_allow_scenarios(
    allowed: set[RBACElementRef],
    batch: list[RBACElementRef],
    expected_processed: list[RBACElementRef],
) -> None:
    processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
        func=_echo_func(),
        validators=[_AllowSetValidator(allowed=allowed)],
    )
    action = _MockBulkAction(element_refs=batch)

    outcome = await processor.wait_for_complete(action)

    assert outcome.result.processed_refs == expected_processed
