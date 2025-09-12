import uuid
from dataclasses import dataclass

from ai.backend.common.dto.manager.response import ObjectStorageResponse


@dataclass
class ObjectStorageData:
    id: uuid.UUID
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str

    def to_dto(self) -> ObjectStorageResponse:
        return ObjectStorageResponse(
            id=str(self.id),
            name=self.name,
            host=self.host,
            access_key=self.access_key,
            secret_key=self.secret_key,
            endpoint=self.endpoint,
            region=self.region,
        )
