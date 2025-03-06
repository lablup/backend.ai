import uuid
from typing import Optional

from pydantic import AliasChoices, BaseModel, Field


class ListGroupQuery(BaseModel):
    group_id: Optional[uuid.UUID] = Field(
        default=None, validation_alias=AliasChoices("group_id", "groupId")
    )
