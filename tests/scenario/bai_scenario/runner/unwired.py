"""Standing in for a dependency a scenario did not wire, and refusing to answer for it.

A service takes what it needs whether or not the scenario under test reaches all of it.
The choice is between handing over a mock, which answers anything and hides that the
test never decided what the answer should be, and handing over something that refuses.
This refuses, and says which dependency and which scenario has to make up its mind.
"""

from __future__ import annotations

from typing import Any, cast


class NotWired(AssertionError):
    """Raised when a scenario reaches a dependency it never wired."""


class _Unwired:
    __slots__ = ("_cls_name", "_why")

    def __init__(self, cls_name: str, why: str) -> None:
        object.__setattr__(self, "_cls_name", cls_name)
        object.__setattr__(self, "_why", why)

    def _refuse(self, what: str) -> NotWired:
        name = object.__getattribute__(self, "_cls_name")
        why = object.__getattribute__(self, "_why")
        return NotWired(
            f"this scenario reached {name}.{what}, which it did not wire ({why}). "
            f"Give the wiring a real {name} or a typed fake that says what it answers."
        )

    def __getattr__(self, name: str) -> Any:
        raise self._refuse(name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise self._refuse("__call__")


def unwired[T](cls: type[T], why: str) -> T:
    """A stand-in for ``cls`` that raises as soon as anything reads it.

    Typed as the class so the constructor that demands it is satisfied, and inert so a
    scenario that turns out to need it fails saying which one it is.
    """
    return cast(T, _Unwired(cls.__name__, why))
