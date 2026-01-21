from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ModelServiceEndpointMeta:
    service_id: UUID
    endpoint_url: str
