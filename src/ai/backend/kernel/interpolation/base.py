import enum
import re
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from ai.backend.kernel.exception import InvalidServiceDefinition
from ai.backend.kernel.interpolation.types import InterpolationOption


class TokenType(enum.Enum):
    TEXT = enum.auto()
    EXPR = enum.auto()


class BaseServiceInterpolator(ABC):
    """Stateless; one instance per syntax is shared, and each call passes its own values."""

    @abstractmethod
    def pattern(self, option: InterpolationOption) -> re.Pattern[str]:
        """Matches one variable reference; its non-empty named group is the expression."""
        raise NotImplementedError

    def apply(
        self, parts: list[str], variables: Mapping[str, Any], option: InterpolationOption
    ) -> list[str]:
        pattern = self.pattern(option)
        return [self._interpolate(part, pattern, variables) for part in parts]

    def render(self, value: str, variables: Mapping[str, Any], option: InterpolationOption) -> str:
        """Interpolate one pre-start action argument."""
        return self._interpolate(value, self.pattern(option), variables)

    def _value_error_hint(self) -> str:
        return ""

    def _interpolate(
        self, part: str, pattern: re.Pattern[str], variables: Mapping[str, Any]
    ) -> str:
        tokens = []
        for token_type, token in self._tokenize(part, pattern):
            match token_type:
                case TokenType.TEXT:
                    tokens.append(token)
                case TokenType.EXPR:
                    tokens.append(self._evaluate(part, token, variables))
        return "".join(tokens)

    @staticmethod
    def _tokenize(s: str, pattern: re.Pattern[str]) -> Iterator[tuple[TokenType, str]]:
        last_index = 0
        for match in pattern.finditer(s):
            start, end = match.span()
            if last_index < start:
                yield TokenType.TEXT, s[last_index:start]
            yield TokenType.EXPR, next(g for g in match.groupdict().values() if g is not None)
            last_index = end
        if last_index < len(s):
            yield TokenType.TEXT, s[last_index:]

    def _evaluate(self, part: str, expr: str, variables: Mapping[str, Any]) -> str:
        try:
            return ("{" + expr + "}").format_map(variables)
        except (KeyError, IndexError) as e:
            raise InvalidServiceDefinition(
                f"Cannot interpolate service argument {part!r}: undefined template variable {e}."
            ) from e
        except ValueError as e:
            raise InvalidServiceDefinition(
                f"Cannot interpolate service argument {part!r}: {e}.{self._value_error_hint()}"
            ) from e


@dataclass(frozen=True)
class BoundInterpolator:
    """A shared interpolator with the values of one service start, handed to pre-start actions."""

    interpolator: BaseServiceInterpolator
    variables: Mapping[str, Any]
    option: InterpolationOption

    def apply(self, parts: list[str]) -> list[str]:
        return self.interpolator.apply(parts, self.variables, self.option)

    def render(self, value: str) -> str:
        return self.interpolator.render(value, self.variables, self.option)
