import uuid
from dataclasses import dataclass


@dataclass
class AssociationArtifactsStoragesData:
    id: uuid.UUID
    artifact_id: uuid.UUID
    storage_id: uuid.UUID
