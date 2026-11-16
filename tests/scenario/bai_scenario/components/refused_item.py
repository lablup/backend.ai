from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.testutils.scenario_steps import Refused, Says, Told, Verdict


@dataclass(frozen=True)
class RefusedItem(Verdict):
    """여럿을 받는 호출이 이 항목 하나를 이 이름의 거부로 실패 목록에 돌려준다.

    레포트는 거부 말머리로 이 행을 거부 행으로 센다. 실패 이유는 `reason`을 담는다.
    """

    called: str
    expected: type[BaseException]
    reason: str
    message: str | None

    @override
    def told(self) -> Told:
        says = Says(
            f"{Refused.PREFIX}{self.called}: {self.expected.__name__}",
            english=f"rejected: {self.called}: {self.expected.__name__}",
        )
        if self.message is None:
            return Told(says, problems=(f"{says} 이어야 하는데 실패 목록에 없다",))
        if self.reason not in self.message:
            return Told(says, problems=(f"{says} 이어야 하는데 이유가 '{self.message}'",))
        return Told(says)
