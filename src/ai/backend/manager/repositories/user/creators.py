"""Creation specs of the user repository beyond the insert spec itself.

The insert spec is :class:`ai.backend.manager.models.user.creators.UserCreator`, and
the write runs through :class:`~.ops.v2.user.write.V2UserWriteOps`.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.models.user.creators import UserCreator


@dataclass
class UserCreateSpec:
    """Specification for creating a single user, including group assignments."""

    creator: UserCreator
    group_ids: list[str] | None = None
