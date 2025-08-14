import uuid
from dataclasses import dataclass


@dataclass
class ImportArtifactTarget:
    artifact_id: uuid.UUID
    storage_id: uuid.UUID
