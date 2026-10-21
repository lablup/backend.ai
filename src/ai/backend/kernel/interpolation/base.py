import enum
import re
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from typing import Any, Self

from ai.backend.kernel.exception import InvalidServiceDefinition
from ai.backend.kernel.interpolation.types import InterpolationOption


class TokenType(enum.Enum):
    TEXT = enum.auto()
    EXPR = enum.auto()


class AbstractServiceInterpolator(ABC):
    _variables: Mapping[str, Any]

    def __init__(self, variables: Mapping[str, Any]) -> None:
        self._variables = variables

    @classmethod
    @abstractmethod
    def from_option(cls, variables: Mapping[str, Any], option: InterpolationOption) -> Self:
        raise NotImplementedError

    @property
    @abstractmethod
    def pattern(self) -> re.Pattern[str]:
        """Matches one variable reference; its non-empty named group is the expression."""
        raise NotImplementedError

    def apply(self, parts: list[str]) -> list[str]:
        return [self._interpolate(part) for part in parts]

    def render(self, value: str) -> str:
        """Interpolate one pre-start action argument."""
        return self._interpolate(value)

    def _interpolate(self, part: str) -> str:
        tokens = []
        for token_type, token in self._tokenize(part):
            match token_type:
                case TokenType.TEXT:
                    tokens.append(token)
                case TokenType.EXPR:
                    tokens.append(self._evaluate(part, token))
        return "".join(tokens)

    def _tokenize(self, s: str) -> Iterator[tuple[TokenType, str]]:
        last_index = 0
        for match in self.pattern.finditer(s):
            start, end = match.span()
            if last_index < start:
                yield TokenType.TEXT, s[last_index:start]
            yield TokenType.EXPR, next(g for g in match.groupdict().values() if g is not None)
            last_index = end
        if last_index < len(s):
            yield TokenType.TEXT, s[last_index:]

    def _evaluate(self, part: str, expr: str) -> str:
        try:
            return ("{" + expr + "}").format_map(self._variables)
        except (KeyError, IndexError) as e:
            raise InvalidServiceDefinition(
                f"Cannot interpolate service argument {part!r}: undefined template variable {e}."
            ) from e
        except ValueError as e:
            raise InvalidServiceDefinition(
                f"Cannot interpolate service argument {part!r}: {e}. "
                "Literal braces (e.g. JSON like vLLM '--hf-overrides') "
                "are not supported."
            ) from e
