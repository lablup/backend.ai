from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import timedelta
from typing import override

from ai.backend.common.data.idle_checker.types import (
    IdleCheckPhase,
    UtilizationSpec,
    UtilizationThresholdOperator,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationBatchAction,
    SessionUtilizationCheck,
)
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleCheckerContext,
    IdleJudgment,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class UtilizationChecker(IdleChecker):
    """Judge session utilization from agent-emitted Prometheus metrics."""

    _metric_service: MetricService

    def __init__(self, metric_service: MetricService) -> None:
        self._metric_service = metric_service

    @override
    async def judge(
        self,
        assignments: Sequence[CheckerAssignment],
        *,
        context: IdleCheckerContext,
    ) -> Sequence[IdleJudgment]:
        # Unknown sessions are ignored because their utilization status cannot be determined.
        assignment_specs: list[tuple[CheckerAssignment, UtilizationSpec]] = []
        checks: list[SessionUtilizationCheck] = []
        for assignment in assignments:
            spec = assignment.definition.spec.utilization
            if spec is None:
                log.error(
                    "Utilization checker has mismatched spec type: checker_id={} spec_type={}",
                    assignment.definition.checker_id,
                    assignment.definition.spec.type,
                )
                continue
            assignment_specs.append((assignment, spec))
            checks.append(
                SessionUtilizationCheck(
                    spec=spec,
                    session_ids=[session.session_id for session in assignment.sessions],
                )
            )
        if not checks:
            return []
        result = await self._metric_service.query_session_utilization_batch(
            SessionUtilizationBatchAction(
                checks=checks,
                evaluation_time=context.current_time,
            )
        )
        judgments: list[IdleJudgment] = []
        for (assignment, spec), observations_by_session in zip(
            assignment_specs,
            result.observations_by_check,
            strict=True,
        ):
            for session in assignment.sessions:
                observations = observations_by_session.get(session.session_id)
                if not observations:
                    continue
                underutilized = [observation.is_underutilized for observation in observations]
                is_idle = (
                    all(underutilized)
                    if spec.thresholds_check_operator is UtilizationThresholdOperator.AND
                    else any(underutilized)
                )
                if is_idle:
                    expire_at = session.expire_at
                    status = (
                        IdleCheckPhase.IDLE_EXPIRED
                        if expire_at <= context.current_time
                        else IdleCheckPhase.IDLE
                    )
                else:
                    expire_at = context.current_time + timedelta(
                        seconds=spec.max_underutilized_duration_seconds
                    )
                    status = IdleCheckPhase.ACTIVE
                details = ", ".join(observation.render() for observation in observations)
                judgments.append(
                    IdleJudgment(
                        checker_id=assignment.definition.checker_id,
                        session_id=session.session_id,
                        expire_at=expire_at,
                        status=status,
                        message=(
                            "Utilization check: "
                            f"max_underutilized_duration_seconds="
                            f"{spec.max_underutilized_duration_seconds}, "
                            f"thresholds_check_operator="
                            f"{spec.thresholds_check_operator.value}, "
                            f"metrics=[{details}]"
                        ),
                    )
                )
        return judgments
