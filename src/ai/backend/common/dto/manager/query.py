import uuid
from typing import Optional

from pydantic import Field

from ...api_handlers import BaseRequestModel


class ListGroupQuery(BaseRequestModel):
    group_id: Optional[uuid.UUID] = Field(default=None, alias="groupId")
