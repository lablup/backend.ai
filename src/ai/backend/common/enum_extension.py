from __future__ import annotations

import enum

__all__ = ("StringSetFlag",)


class StringSetFlag(enum.StrEnum):
    def __eq__(self, other) -> bool:
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)

    def __or__(self, other) -> set[str]:
        if isinstance(other, type(self)):
            other = other.value
        if not isinstance(other, (set, frozenset)):
            other = {other}
        return {self.value} | other

    __ror__ = __or__

    def __and__(self, other) -> bool:
        if isinstance(other, (set, frozenset)):
            return self.value in other
        if isinstance(other, str):
            return self.value == other
        raise TypeError

    __rand__ = __and__

    def __xor__(self, other) -> set[str] | str:
        if isinstance(other, (set, frozenset)):
            return {self.value} ^ other
        if isinstance(other, str):
            if other == self.value:
                return set()
            return other
        raise TypeError

    def __rxor__(self, other) -> set[str] | str:
        if isinstance(other, (set, frozenset)):
            return set(other) ^ {self.value}
        if isinstance(other, str):
            if other == self.value:
                return set()
            return other
        raise TypeError

    def __str__(self) -> str:
        return self.value
