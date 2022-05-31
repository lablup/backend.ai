from __future__ import annotations

import enum

__all__ = (
    'StringSetFlag',
)


class StringSetFlag(enum.Flag):

    def __eq__(self, other):
        return self.value == other

    def __hash__(self):
        return hash(self.value)

    def __or__(self, other):
        if isinstance(other, type(self)):
            other = other.value
        if not isinstance(other, (set, frozenset)):
            other = set((other,))
        return set((self.value,)) | other

    __ror__ = __or__

    def __and__(self, other):
        if isinstance(other, (set, frozenset)):
            return self.value in other
        if isinstance(other, str):
            return self.value == other
        raise TypeError

    __rand__ = __and__

    def __xor__(self, other):
        if isinstance(other, (set, frozenset)):
            return set((self.value,)) ^ other
        if isinstance(other, str):
            if other == self.value:
                return set()
            else:
                return other
        raise TypeError

    def __rxor__(self, other):
        if isinstance(other, (set, frozenset)):
            return other ^ set((self.value,))
        if isinstance(other, str):
            if other == self.value:
                return set()
            else:
                return other
        raise TypeError

    def __str__(self):
        return self.value
