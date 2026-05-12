import uuid

from ai.backend.common.types import BackendAISchema

from .object_type import ObjectType


class UOID(BackendAISchema):
    uuid: uuid.UUID
    objectType: ObjectType
