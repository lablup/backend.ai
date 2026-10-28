import functools
import re
from collections.abc import Mapping, Sequence
from typing import Any, Final

from ai.backend.kernel.exception import InvalidServiceDefinition
from ai.backend.kernel.interpolation.types import InterpolationDelimiter

# The syntax image service-defs are written in: ``${{ var }}`` (github-style) and ``{var}`` (python-style).
LEGACY_DELIMITERS: Final[Sequence[InterpolationDelimiter]] = (
    {"start": "${{", "end": "}}"},
    {"start": "{", "end": "}"},
)


class ServiceInterpolator:
    """Fills the variables of one service start into its command, envs and pre-start action args."""

    _variables: Mapping[str, Any]
    _delimiters: tuple[InterpolationDelimiter, ...]

    def __init__(
        self, variables: Mapping[str, Any], delimiters: Sequence[InterpolationDelimiter]
    ) -> None:
        if not delimiters:
            raise InvalidServiceDefinition("Service interpolation requires at least one delimiter")
        self._variables = variables
        self._delimiters = tuple(delimiters)

    def apply(self, parts: list[str]) -> list[str]:
        pattern = self._compile(tuple((d["start"], d["end"]) for d in self._delimiters))
        return [pattern.sub(self._evaluate, part) for part in parts]

    @staticmethod
    @functools.cache
    def _compile(delimiters: tuple[tuple[str, str], ...]) -> re.Pattern[str]:
        # A start right after ``$`` or ``{`` stays, so shell expansions such as ``${HOME}`` are untouched.
        alternatives = []
        for index, (start, end) in enumerate(delimiters):
            alternatives.append(
                rf"(?<![${{]){re.escape(start)}\s*(?P<expr{index}>.*?)\s*{re.escape(end)}"
            )
        return re.compile("|".join(alternatives))

    def _evaluate(self, match: re.Match[str]) -> str:
        expr = next(group for group in match.groups() if group is not None)
        try:
            return ("{" + expr + "}").format_map(self._variables)
        except (KeyError, IndexError) as e:
            raise InvalidServiceDefinition(
                f"Cannot interpolate service argument {match.string!r}: undefined template variable {e}."
            ) from e
        except ValueError as e:
            hint = (
                " Literal braces (e.g. JSON like vLLM '--hf-overrides') are not supported."
                if any(d["start"] == "{" for d in self._delimiters)
                else ""
            )
            raise InvalidServiceDefinition(
                f"Cannot interpolate service argument {match.string!r}: {e}.{hint}"
            ) from e
