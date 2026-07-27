from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import timedelta
from typing import override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase, UtilizationSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.idle_checker.types import IdleJudgmentData
from ai.backend.manager.services.metric.actions.session_utilization import (
    SessionUtilizationAction,
    SessionUtilizationQuery,
)
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleCheckerContext,
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
    ) -> Sequence[IdleJudgmentData]:
        # Unknown sessions are ignored because their utilization status cannot be determined.
        valid_assignments: list[tuple[CheckerAssignment, UtilizationSpec]] = []
        queries: list[SessionUtilizationQuery] = []
        for assignment in assignments:
            spec = assignment.definition.spec.utilization
            if spec is None:
                log.error(
                    "Utilization checker has mismatched spec type: checker_id={} spec_type={}",
                    assignment.definition.checker_id,
                    assignment.definition.spec.type,
                )
                continue
            valid_assignments.append((assignment, spec))
            queries.append(
                SessionUtilizationQuery(
                    preset_id=spec.threshold.preset_id,
                    session_ids=[session.session_id for session in assignment.sessions],
                )
            )
        if not queries:
            return []

        result = await self._metric_service.query_session_utilization(
            SessionUtilizationAction(
                queries=queries,
                evaluation_time=context.current_time,
            )
        )
        judgments: list[IdleJudgmentData] = []
        for assignment, spec in valid_assignments:
            threshold = spec.threshold
            observations = result.observations_by_preset.get(threshold.preset_id, {})
            for session in assignment.sessions:
                observation = observations.get(session.session_id)
                if observation is None:
                    continue
                is_idle = observation.value < threshold.threshold
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
                judgments.append(
                    IdleJudgmentData(
                        checker_id=assignment.definition.checker_id,
                        session_id=session.session_id,
                        expire_at=expire_at,
                        status=status,
                        message=(
                            "Utilization check: "
                            f"max_underutilized_duration_seconds="
                            f"{spec.max_underutilized_duration_seconds}, "
                            f"metric=[preset_id={observation.preset_id}, "
                            f"value={observation.value:f}/{threshold.threshold:f}]"
                        ),
                    )
                )
        return judgments
