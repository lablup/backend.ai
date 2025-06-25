import uuid
from dataclasses import dataclass


@dataclass
class CreatedModelServiceMeta:
    endpoint_id: uuid.UUID
    service_endpoint: str
