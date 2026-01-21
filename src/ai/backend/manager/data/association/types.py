import uuid
from dataclasses import dataclass


@dataclass
class AssociationArtifactsStoragesData:
    id: uuid.UUID
    artifact_revision_id: uuid.UUID
    storage_namespace_id: uuid.UUID
