import uuid

from pydantic import BaseModel

from .object_type import ObjectType


class UOID(BaseModel):
    uuid: uuid.UUID
    objectType: ObjectType
