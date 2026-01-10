"""Utility functions for converting recorder types to domain types."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar

from ai.backend.manager.data.session.types import SchedulingResult, SubStepResult
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord, StepRecord, StepStatus

EntityIdT = TypeVar("EntityIdT")


def step_record_to_sub_step_result(step: StepRecord) -> SubStepResult:
    """Convert recorder StepRecord to SubStepResult for history storage."""
    result = (
        SchedulingResult.SUCCESS if step.status == StepStatus.SUCCESS else SchedulingResult.FAILURE
    )
    return SubStepResult(
        step=step.name,
        result=result,
        error_code=None,  # StepRecord doesn't have error_code
        message=step.detail,
        started_at=step.started_at,
        ended_at=step.ended_at,
    )


def extract_sub_steps_for_entity(
    entity_id: EntityIdT,
    records: Mapping[EntityIdT, ExecutionRecord],
) -> list[SubStepResult]:
    """Extract sub_steps for a specific entity from records mapping.

    Args:
        entity_id: The entity ID (SessionId, DeploymentId, etc.) to extract steps for.
        records: A mapping of entity IDs to their ExecutionRecords.

    Returns:
        A list of SubStepResult objects extracted from all phases and steps.
    """
    record = records.get(entity_id)
    if record is None:
        return []

    sub_steps: list[SubStepResult] = []
    for phase in record.phases:
        for step in phase.steps:
            sub_steps.append(step_record_to_sub_step_result(step))
    return sub_steps
