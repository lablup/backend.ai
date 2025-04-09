import uuid
from typing import Optional

from pydantic import BaseModel, Field


class ListGroupQuery(BaseModel):
    group_id: Optional[uuid.UUID] = Field(default=None, alias="groupId")
