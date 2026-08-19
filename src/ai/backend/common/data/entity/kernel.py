"""Id of the kernels table.

A kernel runs under a session and carries no membership of its own, so its id is a
field identifier: what a kernel belongs to is knowable only through that session.
"""

from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("KernelID",)


class KernelID(FieldIdentifier):
    """A kernel row's id."""

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE
