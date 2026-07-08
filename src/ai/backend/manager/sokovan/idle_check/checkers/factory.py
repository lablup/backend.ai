"""Static dispatch from a definition's checker_type to its implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from ai.backend.common.data.idle_checker.types import CheckerType
from ai.backend.manager.sokovan.idle_check.checkers.base import IdleChecker

# Concrete checker types register here as their stories land.
_CHECKERS: Final[Mapping[CheckerType, IdleChecker[Any]]] = {}


def checker_for(checker_type: CheckerType) -> IdleChecker[Any] | None:
    return _CHECKERS.get(checker_type)
