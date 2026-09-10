"""세 단계로 된 시나리오. 각 단계가 무엇을 했는지 스스로 말한다.

`given`이 먼저 돌아 값을 답한다. `when`은 그 값과 어댑터만 받는다. `then`은 심은 것과 답
또는 예외를 함께 받는다. 앞 단계가 이미 돌았으므로 값을 미뤄 두기 위한 장치가 없다.

레포트는 이 단계들이 답한 말로만 만들어진다. 무시한 자리는 무시했다고, 값을 본 자리는 그
값으로, 조건으로만 본 자리는 그 조건으로 말한다. 조건에는 실제 값을 넣지 않는다. 넣으면
같은 동작인데도 실행마다 레포트가 달라진다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import override


@dataclass(frozen=True)
class Answered[R]:
    """호출이 답한 것. 답이 왔거나 예외로 막혔거나 둘 중 하나다."""

    response: R | None = None
    raised: BaseException | None = None

    def refused(self) -> bool:
        return self.raised is not None


@dataclass(frozen=True)
class Told:
    """한 단계가 한 일. 안에 품은 것은 그 아래로 쌓인다."""

    says: str
    problems: tuple[str, ...] = ()
    within: tuple[Told, ...] = field(default_factory=tuple)

    def lines(self, depth: int = 0) -> list[str]:
        out = [f"{'  ' * depth}- {self.says}"]
        for one in self.within:
            out.extend(one.lines(depth + 1))
        return out

    def every_problem(self) -> list[str]:
        out = list(self.problems)
        for one in self.within:
            out.extend(one.every_problem())
        return out


class Condition[V](ABC):
    """값을 값으로 말할 수 없을 때 대신 거는 것.

    무엇을 만족해야 하는지 스스로 말하고, 그 말에 실제 값을 넣지 않는다.
    """

    @abstractmethod
    def says(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def holds(self, got: V) -> bool:
        raise NotImplementedError


class Verdict(ABC):
    """한 자리를 어떻게 보았는지."""

    @abstractmethod
    def told(self) -> Told:
        raise NotImplementedError


@dataclass(frozen=True)
class Same[V](Verdict):
    """이 값이어야 한다. 시나리오가 정한 값이므로 레포트에 그대로 적는다."""

    called: str
    got: V
    wanted: V

    @override
    def told(self) -> Told:
        if self.got == self.wanted:
            return Told(f"{self.called} = {self.wanted!r}")
        return Told(
            f"{self.called} = {self.wanted!r}",
            problems=(f"{self.called}: {self.wanted!r} 이어야 하는데 {self.got!r}",),
        )


@dataclass(frozen=True)
class Skipped(Verdict):
    """보지 않는다. 왜 보지 않는지는 적는다."""

    called: str
    why: str

    @override
    def told(self) -> Told:
        return Told(f"{self.called}: 무시함 — {self.why}")


@dataclass(frozen=True)
class Held[V](Verdict):
    """값으로는 말할 수 없어 조건으로 본다."""

    called: str
    got: V
    condition: Condition[V]

    @override
    def told(self) -> Told:
        if self.condition.holds(self.got):
            return Told(f"{self.called}: {self.condition.says()}")
        return Told(
            f"{self.called}: {self.condition.says()}",
            problems=(f"{self.called}: {self.condition.says()} 이어야 하는데 아니다",),
        )


@dataclass(frozen=True)
class Refused(Verdict):
    """이 이름으로 거부되어야 한다."""

    expected: type[BaseException]
    raised: BaseException | None

    @override
    def told(self) -> Told:
        says = f"거부: {self.expected.__name__}"
        if self.raised is None:
            return Told(says, problems=(f"{says} 이어야 하는데 답이 왔다",))
        if not isinstance(self.raised, self.expected):
            return Told(says, problems=(f"{says} 이어야 하는데 {type(self.raised).__name__}",))
        return Told(says)


class Given[S, G](ABC):
    """요청 시점에 이미 참이어야 하는 것을 세우고, 세운 것을 답한다.

    ``S``는 행을 심는 자리, ``G``는 세운 것이다. 여기는 어느 컴포넌트도 모르므로 심는
    자리의 타입도 밖에서 온다.
    """

    @abstractmethod
    def describe(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def lay(self, seeding: S) -> G:
        raise NotImplementedError


class When[G, A, R](ABC):
    """어댑터를 부른다. `given`이 답한 값과 어댑터 말고는 받지 않는다."""

    @abstractmethod
    def operation(self) -> str:
        """어느 어댑터 호출을 하는지. 레포트가 이것으로 미실행 호출을 센다."""
        raise NotImplementedError

    @abstractmethod
    def describe(self, laid: G) -> str:
        """무엇을 부르는지. 심은 것을 알고 나서 말하므로 그 값을 쓸 수 있다."""
        raise NotImplementedError

    @abstractmethod
    async def call(self, adapter: A, laid: G) -> R:
        raise NotImplementedError


class Then[G, R](ABC):
    """답 또는 거부를 본다. 무엇을 어떻게 보았는지 자리마다 답한다."""

    @abstractmethod
    def says(self) -> str:
        """무엇을 보는지 한 줄로."""
        raise NotImplementedError

    @abstractmethod
    def look(self, laid: G, answered: Answered[R]) -> list[Verdict]:
        raise NotImplementedError

    def told(self, laid: G, answered: Answered[R]) -> Told:
        """본 것을 그대로 쌓는다."""
        seen = [one.told() for one in self.look(laid, answered)]
        return Told(self.says(), within=tuple(seen))


class Scenario[S, G, A, R](ABC):
    """한 시나리오. 이름과 보장하는 것, 그리고 세 단계."""

    @abstractmethod
    def summary(self) -> str:
        """kebab 영문 요약. pytest 파라미터 id로도 쓰인다."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        """이 행이 무엇을 보장하는지 한 문장."""
        raise NotImplementedError

    @abstractmethod
    def given(self) -> Given[S, G]:
        raise NotImplementedError

    @abstractmethod
    def when(self) -> When[G, A, R]:
        raise NotImplementedError

    @abstractmethod
    def then(self) -> Then[G, R]:
        raise NotImplementedError
