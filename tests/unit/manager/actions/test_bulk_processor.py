"""Tests for ``BulkActionProcessor`` filtering infrastructure (BA-5777).

Verifies that the processor narrows ``entity_ids`` exactly to what each
validator allowed — no more, no less — and that later validators only
see IDs that survived earlier ones.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import EntityType
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


@dataclass
class _MockBulkAction(BaseBulkAction[str]):
    @override
    def typed_entity_ids(self) -> list[str]:
        return list(self.entity_ids)

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
    processed_ids: list[str] = field(default_factory=list)

    @override
    def entity_ids(self) -> list[str]:
        return list(self.processed_ids)


class _AllowSetValidator(BulkActionValidator):
    """Approves any ID in ``allowed``; anything else visible is denied."""

    def __init__(self, allowed: set[str], name: str = "allow-set") -> None:
        self._allowed = set(allowed)
        self._name = name

    @classmethod
    @override
    def name(cls) -> str:
        return "allow-set"

    @override
    async def validate(
        self, action: BaseBulkAction[Any], meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        current = list(action.entity_ids)
        allowed = [eid for eid in current if eid in self._allowed]
        denied = [
            DeniedEntity(entity_id=eid, deny_reason="not in allow-set")
            for eid in current
            if eid not in self._allowed
        ]
        return BulkValidationResult(allowed_entity_ids=allowed, denied_entities=denied)


class _RecordingValidator(BulkActionValidator):
    """Captures the entity IDs each ``validate()`` call received."""

    def __init__(self, allowed: set[str]) -> None:
        self._allowed = set(allowed)
        self.observed_batches: list[list[str]] = []

    @classmethod
    @override
    def name(cls) -> str:
        return "recording"

    @override
    async def validate(
        self, action: BaseBulkAction[Any], meta: BaseActionTriggerMeta
    ) -> BulkValidationResult:
        current = list(action.entity_ids)
        self.observed_batches.append(current)
        allowed = [eid for eid in current if eid in self._allowed]
        denied = [
            DeniedEntity(entity_id=eid, deny_reason="blocked")
            for eid in current
            if eid not in self._allowed
        ]
        return BulkValidationResult(allowed_entity_ids=allowed, denied_entities=denied)


def _echo_func() -> Callable[[_MockBulkAction], Awaitable[_MockBulkActionResult]]:
    async def _run(action: _MockBulkAction) -> _MockBulkActionResult:
        return _MockBulkActionResult(processed_ids=list(action.entity_ids))

    return _run


class TestBulkActionProcessorFiltering:
    async def test_no_validators_passes_all_ids_through(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
        )
        action = _MockBulkAction(entity_ids=["a", "b", "c"])

        outcome = await processor.wait_for_complete(action)

        assert outcome.result.processed_ids == ["a", "b", "c"]
        assert outcome.validator_decisions == []

    async def test_validator_denies_subset_reports_denied_ids(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={"a", "c"})],
        )
        action = _MockBulkAction(entity_ids=["a", "b", "c"])

        outcome = await processor.wait_for_complete(action)

        assert outcome.result.processed_ids == ["a", "c"]
        assert len(outcome.validator_decisions) == 1
        decision = outcome.validator_decisions[0]
        assert decision.validator_name == "allow-set"
        assert decision.results.allowed_entity_ids == ["a", "c"]
        assert decision.results.denied_entities == [
            DeniedEntity(entity_id="b", deny_reason="not in allow-set"),
        ]

    async def test_validator_denies_all_still_runs_service_with_empty_batch(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed=set())],
        )
        action = _MockBulkAction(entity_ids=["a", "b"])

        outcome = await processor.wait_for_complete(action)

        assert outcome.result.processed_ids == []
        decision = outcome.validator_decisions[0]
        assert decision.results.allowed_entity_ids == []
        assert [d.entity_id for d in decision.results.denied_entities] == ["a", "b"]

    async def test_later_validator_only_sees_surviving_ids(self) -> None:
        first = _RecordingValidator(allowed={"a", "b"})
        second = _RecordingValidator(allowed={"a"})
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[first, second],
        )
        action = _MockBulkAction(entity_ids=["a", "b", "c"])

        outcome = await processor.wait_for_complete(action)

        # First validator sees the full batch; second only sees IDs that
        # survived the first.
        assert first.observed_batches == [["a", "b", "c"]]
        assert second.observed_batches == [["a", "b"]]

        assert outcome.result.processed_ids == ["a"]
        assert [
            (
                d.validator_name,
                d.results.allowed_entity_ids,
                [de.entity_id for de in d.results.denied_entities],
            )
            for d in outcome.validator_decisions
        ] == [
            ("recording", ["a", "b"], ["c"]),
            ("recording", ["a"], ["b"]),
        ]

    async def test_original_action_is_not_mutated(self) -> None:
        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_echo_func(),
            validators=[_AllowSetValidator(allowed={"a"})],
        )
        original = _MockBulkAction(entity_ids=["a", "b"])

        outcome = await processor.wait_for_complete(original)

        assert outcome.result.processed_ids == ["a"]
        # The processor constructs a fresh action; it must not mutate the caller's.
        assert original.entity_ids == ["a", "b"]

    async def test_pass_through_reuses_same_action_instance(self) -> None:
        seen: list[_MockBulkAction] = []

        async def _capture(action: _MockBulkAction) -> _MockBulkActionResult:
            seen.append(action)
            return _MockBulkActionResult(processed_ids=list(action.entity_ids))

        processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
            func=_capture,
            validators=[_AllowSetValidator(allowed={"a", "b"})],
        )
        original = _MockBulkAction(entity_ids=["a", "b"])

        await processor.wait_for_complete(original)

        # No denials → no filtering copy was created.
        assert seen[0] is original


@pytest.mark.parametrize(
    ("allowed", "batch", "expected_processed"),
    [
        ({"a", "b"}, ["a", "b"], ["a", "b"]),
        ({"a"}, ["a", "b"], ["a"]),
        (set(), ["a", "b"], []),
    ],
)
async def test_single_validator_scenarios(
    allowed: set[str],
    batch: list[str],
    expected_processed: list[str],
) -> None:
    processor = BulkActionProcessor[_MockBulkAction, _MockBulkActionResult](
        func=_echo_func(),
        validators=[_AllowSetValidator(allowed=allowed)],
    )
    action = _MockBulkAction(entity_ids=batch)

    outcome = await processor.wait_for_complete(action)

    assert outcome.result.processed_ids == expected_processed
