"""User-config adapter inputs after resolving the owning user."""

from dataclasses import dataclass

from ai.backend.common.data.entity.user import UserID


@dataclass(frozen=True)
class CreateDotfileInput:
    user_id: UserID
    path: str
    perm: str
    data: str


@dataclass(frozen=True)
class UpdateDefaultDotfileInput:
    user_id: UserID
    path: str
    perm: str
    data: str


@dataclass(frozen=True)
class DeleteDefaultDotfileInput:
    user_id: UserID
    path: str
