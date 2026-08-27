from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.auth import InvalidUserLookupData


@dataclass(frozen=True)
class UserLookupData:
    """The key naming the account a request belongs to.

    The manager takes the first field set, in the order declared here.
    """

    user_id: UserID | None = None
    email: str | None = None
    username: str | None = None
    access_key: AccessKey | None = None

    def __post_init__(self) -> None:
        if not any((self.user_id, self.email, self.username, self.access_key)):
            raise InvalidUserLookupData("The lookup data names no account.")
