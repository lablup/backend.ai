from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import override

from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleChecker,
    IdleJudgment,
)


class SessionLifetimeChecker(IdleChecker):
    """Judge sessions solely against each checker definition's lifetime setting."""

    @override
    async def judge(
        self,
        assignments: Sequence[CheckerAssignment],
        *,
        current_time: datetime,
    ) -> Sequence[IdleJudgment]:
        judgments: list[IdleJudgment] = []
        for assignment in assignments:
            lifetime_spec = assignment.definition.spec.session_lifetime
            if lifetime_spec is None:
                raise InternalServerError(
                    f"Session lifetime checker(id: {assignment.definition.checker_id}) received an empty spec."
                )
            if lifetime_spec.max_lifetime_seconds == 0:
                continue
            max_lifetime_seconds = Decimal(lifetime_spec.max_lifetime_seconds)
            for session in assignment.sessions:
                if session.starts_at is None:
                    continue
                running_seconds = Decimal(
                    str((current_time - session.starts_at).total_seconds())
                ).normalize()
                judgments.append(
                    IdleJudgment(
                        checker_id=assignment.definition.checker_id,
                        session_id=session.session_id,
                        is_idle=running_seconds >= max_lifetime_seconds,
                        message=(
                            "Session lifetime exceeded: "
                            f"max_lifetime_seconds={max_lifetime_seconds:f}, "
                            f"running_seconds={running_seconds:f}"
                        ),
                    )
                )
        return judgments
