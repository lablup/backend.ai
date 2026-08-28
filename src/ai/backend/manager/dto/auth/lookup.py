from __future__ import annotations

from typing import Self

from pydantic import ConfigDict, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.auth import InvalidUserLookupData


class UserLookupData(BaseRequestModel):
    """The key naming the account a request belongs to.

    The manager takes the first field set, in the order declared here.
    """

    model_config = ConfigDict(frozen=True)

    user_id: UserID | None = None
    email: str | None = None
    username: str | None = None
    access_key: AccessKey | None = None

    @model_validator(mode="after")
    def _names_an_account(self) -> Self:
        if not any((self.user_id, self.email, self.username, self.access_key)):
            raise InvalidUserLookupData("The lookup data names no account.")
        return self
