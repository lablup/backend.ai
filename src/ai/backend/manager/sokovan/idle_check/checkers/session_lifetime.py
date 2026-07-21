from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal
from typing import override

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleCheckerContext,
    IdleJudgment,
    IdleJudgmentStatus,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class SessionLifetimeChecker(IdleChecker):
    """Judge sessions solely against each checker definition's lifetime setting."""

    @override
    async def judge(
        self,
        assignments: Sequence[CheckerAssignment],
        *,
        context: IdleCheckerContext,
    ) -> Sequence[IdleJudgment]:
        judgments: list[IdleJudgment] = []
        for assignment in assignments:
            lifetime_spec = assignment.definition.spec.session_lifetime
            if lifetime_spec is None:
                log.error(
                    "Session lifetime checker {} has mismatched spec type: {}",
                    assignment.definition.checker_id,
                    assignment.definition.spec.type,
                )
                continue
            if lifetime_spec.max_lifetime_seconds == 0:
                continue
            max_lifetime_seconds = Decimal(lifetime_spec.max_lifetime_seconds)
            for session in assignment.sessions:
                if session.starts_at is None:
                    continue
                running_seconds = Decimal(
                    str((context.current_time - session.starts_at).total_seconds())
                ).normalize()
                is_idle = running_seconds >= max_lifetime_seconds
                if is_idle:
                    expires_at = session.starts_at + timedelta(
                        seconds=lifetime_spec.max_lifetime_seconds
                    )
                else:
                    expires_at = None
                judgments.append(
                    IdleJudgment(
                        checker_id=assignment.definition.checker_id,
                        session_id=session.session_id,
                        is_idle=is_idle,
                        expire_at=expires_at,
                        status=IdleJudgmentStatus.IDLE if is_idle else IdleJudgmentStatus.BUSY,
                        message=(
                            "Session lifetime check: "
                            f"max_lifetime_seconds={max_lifetime_seconds:f}, "
                            f"running_seconds={running_seconds:f}"
                        ),
                    )
                )
        return judgments
