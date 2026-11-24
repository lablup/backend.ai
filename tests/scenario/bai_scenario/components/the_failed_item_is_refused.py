from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.testutils.scenario_steps import Refused, Says, Told, Verdict


@dataclass(frozen=True)
class TheFailedItemIsRefused(Verdict):
    """A partial bulk answer's failed item, marked as the refusal this row expected.

    The call answers with a failed list instead of raising, so the item's reason is
    checked and the line carries the refusal mark the report counts.
    """

    at: str
    message: str
    reason: str

    @override
    def told(self) -> Told:
        says = Says(
            f"{Refused.PREFIX}{self.at}: {self.reason}",
            f"rejected: {self.at}: {self.reason}",
        )
        if self.reason not in self.message:
            return Told(
                says,
                problems=(f"{self.at}: {self.reason!r} 이어야 하는데 {self.message!r}",),
            )
        return Told(says)
