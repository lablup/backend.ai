"""세 단계로 된 시나리오. 각 단계가 무엇을 했는지 스스로 말한다.

`given`이 먼저 돌아 값을 답한다. `when`은 그 값과 어댑터만 받는다. `then`은 심은 것과 답
또는 예외를 함께 받는다. 앞 단계가 이미 돌았으므로 값을 미뤄 두기 위한 장치가 없다.

레포트는 이 단계들이 답한 말로만 만들어진다. 무시한 자리는 무시했다고, 값을 본 자리는 그
값으로, 조건으로만 본 자리는 그 조건으로 말한다. 조건에는 실제 값을 넣지 않는다. 넣으면
같은 동작인데도 실행마다 레포트가 달라진다.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self, override
from uuid import UUID


class Language(enum.StrEnum):
    """The language a report writes in."""

    ENGLISH = "en"
    KOREAN = "ko"


class Says(str):
    """A sentence in Korean with the English one beside it.

    Formatting it gives the Korean sentence. The report asks for a language, so a
    sentence whose English is not written yet falls back to Korean there, and the
    English report refuses to write it.
    """

    english: str

    def __new__(cls, korean: str, english: str = "") -> Self:
        self = super().__new__(cls, korean)
        self.english = english
        return self

    def in_(self, language: Language) -> str:
        """This sentence in ``language``; English that is not written yet falls back."""
        if language is Language.ENGLISH and self.english:
            return self.english
        return str(self)

    def as_data(self) -> dict[str, str]:
        """Both sentences, for the JSON record a run writes."""
        return {"korean": str(self), "english": self.english}

    @classmethod
    def from_data(cls, raw: str | Mapping[str, str]) -> Says:
        """A record field; a run may have written it as a bare Korean string."""
        if isinstance(raw, Mapping):
            return cls(raw["korean"], raw.get("english", ""))
        return cls(raw)


def in_language(text: str, language: Language) -> str:
    """``text`` in ``language``; a plain string has the same text in either."""
    return text.in_(language) if isinstance(text, Says) else text


def with_particle(text: str, particle: str) -> str:
    """``particle`` after ``text``; spaced when the text ends in a Latin letter or digit."""
    if text and text[-1].isascii() and text[-1].isalnum():
        return f"{text} {particle}"
    return f"{text}{particle}"


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
class SameAs[V](Condition[V]):
    """다른 자리에서 온 값과 같아야 한다.

    그 값이 실행마다 달라지는 것일 때 쓴다. 값 대신 어디서 온 것인지로 말하므로 레포트가
    실행마다 달라지지 않는다.
    """

    wanted: V
    came_from: str

    @override
    def says(self) -> Says:
        return Says(
            with_particle(str(self.came_from), "와 같다"),
            f"same as {in_language(self.came_from, Language.ENGLISH)}",
        )

    @override
    def holds(self, got: V) -> bool:
        return bool(got == self.wanted)


@dataclass(frozen=True)
class Same[V](Verdict):
    """이 값이어야 한다. 시나리오가 정한 값이므로 레포트에 그대로 적는다.

    생성된 id는 값으로 적지 않는다. 실행마다 달라 레포트가 흔들린다. 그런 자리는
    :class:`SameAs`를 조건으로 걸어 어디서 온 값인지로 말한다.
    """

    called: str
    got: V
    wanted: V

    def _shows(self) -> Says:
        if isinstance(self.wanted, UUID):
            raise ValueError(f"{self.called}: 생성된 id를 값으로 적을 수 없다. SameAs 조건을 쓴다")

        def spoken(value: Any, language: Language) -> Any:
            if isinstance(value, Says):
                return value.in_(language)
            if isinstance(value, list):
                return [spoken(one, language) for one in value]
            if isinstance(value, tuple):
                return tuple(spoken(one, language) for one in value)
            if isinstance(value, Mapping):
                return {key: spoken(one, language) for key, one in value.items()}
            return value

        text = f"{self.called} = {spoken(self.wanted, Language.KOREAN)!r}"
        return Says(text, english=f"{self.called} = {spoken(self.wanted, Language.ENGLISH)!r}")

    @override
    def told(self) -> Told:
        says = self._shows()
        if self.got == self.wanted:
            return Told(says)
        return Told(says, problems=(f"{self.called}: {self.wanted!r} 이어야 하는데 {self.got!r}",))


@dataclass(frozen=True)
class Skipped(Verdict):
    """보지 않는다. 왜 보지 않는지는 적는다."""

    called: str
    why: str

    @override
    def told(self) -> Told:
        return Told(
            Says(
                f"{self.called}: 건너뜀: {self.why}",
                f"{self.called}: skipped: {in_language(self.why, Language.ENGLISH)}",
            )
        )


@dataclass(frozen=True)
class Held[V](Verdict):
    """값으로는 말할 수 없어 조건으로 본다."""

    called: str
    got: V
    condition: Condition[V]

    @override
    def told(self) -> Told:
        says = Says(
            f"{self.called}: {self.condition.says()}",
            f"{self.called}: {in_language(self.condition.says(), Language.ENGLISH)}",
        )
        if self.condition.holds(self.got):
            return Told(says)
        return Told(
            says,
            problems=(f"{self.called}: {self.condition.says()} 이어야 하는데 아니다",),
        )


@dataclass(frozen=True)
class Refused(Verdict):
    """이 이름으로 거부되어야 한다."""

    PREFIX: ClassVar[str] = "거부: "
    """레포트가 이 말머리로 거부를 기대한 행을 가려낸다."""

    expected: type[BaseException]
    raised: BaseException | None

    @override
    def told(self) -> Told:
        says = Says(
            f"{self.PREFIX}{self.expected.__name__}",
            f"rejected: {self.expected.__name__}",
        )
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


class Configured(ABC):
    """설정을 바꿔 두고 도는 시나리오가 함께 구현한다.

    바꿀 자리는 설정 파일의 경로다. 표가 행을 잇는 값이 아니라 설정 그 자체이므로 경로로
    적는다.
    """

    @abstractmethod
    def config(self) -> Mapping[str, Any]:
        raise NotImplementedError


class Scenario[S, G, A, R](ABC):
    """한 시나리오. 이름과 보장하는 것, 그리고 세 단계."""

    @abstractmethod
    def summary(self) -> str:
        """kebab 영문 요약. pytest 파라미터 id로도 쓰인다."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        """이 행이 무엇을 보장하는지 한 문장. :class:`Says`면 영어가 함께 나간다."""
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
