import dataclasses
import uuid

from dateutil.parser import isoparse

from ai.backend.manager.data.artifact.types import (
    ArtifactRegistryType,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.models.artifact import ArtifactRow

# Sample artifact fixtures for testing
ARTIFACT_ROW_FIXTURE_1 = ArtifactRow(
    type=ArtifactType.MODEL,
    name="facebook/bart-large-cnn",
    size=1024 * 1024 * 100,  # 100MB
    registry_id=uuid.uuid4(),
    registry_type=ArtifactRegistryType.HUGGINGFACE,
    source_registry_id=uuid.uuid4(),
    source_registry_type=ArtifactRegistryType.HUGGINGFACE,
    description="BART model for CNN summarization",
    readme="This is a BART model fine-tuned for CNN/DailyMail summarization.",
    version="main",
    authorized=True,
    status=ArtifactStatus.VERIFIED.value,
)
ARTIFACT_ROW_FIXTURE_1.id = uuid.uuid4()
ARTIFACT_ROW_FIXTURE_1.created_at = isoparse("2023-10-01T00:00:00+09:00")
ARTIFACT_ROW_FIXTURE_1.updated_at = isoparse("2023-10-01T01:00:00+09:00")

ARTIFACT_ROW_FIXTURE_2 = ArtifactRow(
    type=ArtifactType.MODEL,
    name="microsoft/DialoGPT-small",
    size=1024 * 1024 * 50,  # 50MB
    registry_id=uuid.uuid4(),
    registry_type=ArtifactRegistryType.HUGGINGFACE,
    source_registry_id=uuid.uuid4(),
    source_registry_type=ArtifactRegistryType.HUGGINGFACE,
    description="Small DialoGPT model for conversation",
    readme="DialoGPT is a large-scale tunable neural conversational response generation model.",
    version="main",
    authorized=False,
    status=ArtifactStatus.SCANNED.value,
)
ARTIFACT_ROW_FIXTURE_2.id = uuid.uuid4()
ARTIFACT_ROW_FIXTURE_2.created_at = isoparse("2023-10-02T00:00:00+09:00")
ARTIFACT_ROW_FIXTURE_2.updated_at = isoparse("2023-10-02T01:00:00+09:00")

ARTIFACT_ROW_FIXTURE_3 = ArtifactRow(
    type=ArtifactType.MODEL,
    name="google/bert-base-uncased",
    size=1024 * 1024 * 200,  # 200MB
    registry_id=uuid.uuid4(),
    registry_type=ArtifactRegistryType.HUGGINGFACE,
    source_registry_id=uuid.uuid4(),
    source_registry_type=ArtifactRegistryType.HUGGINGFACE,
    description="BERT base model (uncased)",
    readme="BERT base model (uncased) for various NLP tasks.",
    version="main",
    authorized=True,
    status=ArtifactStatus.VERIFIED.value,
)
ARTIFACT_ROW_FIXTURE_3.id = uuid.uuid4()
ARTIFACT_ROW_FIXTURE_3.created_at = isoparse("2023-10-03T00:00:00+09:00")
ARTIFACT_ROW_FIXTURE_3.updated_at = isoparse("2023-10-03T01:00:00+09:00")

# Convert to dataclass fixtures
ARTIFACT_FIXTURE_DATA_1 = ARTIFACT_ROW_FIXTURE_1.to_dataclass()
ARTIFACT_FIXTURE_DATA_2 = ARTIFACT_ROW_FIXTURE_2.to_dataclass()
ARTIFACT_FIXTURE_DATA_3 = ARTIFACT_ROW_FIXTURE_3.to_dataclass()

# Convert to dictionary fixtures for database insertion
ARTIFACT_FIXTURE_DICT_1 = dataclasses.asdict(
    dataclasses.replace(
        ARTIFACT_FIXTURE_DATA_1,
        type=ArtifactType.MODEL._name_,
        registry_type=ArtifactRegistryType.HUGGINGFACE.value,
        source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
        status=ArtifactStatus.VERIFIED.value,
    )
)

ARTIFACT_FIXTURE_DICT_2 = dataclasses.asdict(
    dataclasses.replace(
        ARTIFACT_FIXTURE_DATA_2,
        type=ArtifactType.MODEL._name_,
        registry_type=ArtifactRegistryType.HUGGINGFACE.value,
        source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
        status=ArtifactStatus.SCANNED.value,
    )
)

ARTIFACT_FIXTURE_DICT_3 = dataclasses.asdict(
    dataclasses.replace(
        ARTIFACT_FIXTURE_DATA_3,
        type=ArtifactType.MODEL._name_,
        registry_type=ArtifactRegistryType.HUGGINGFACE.value,
        source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
        status=ArtifactStatus.VERIFIED.value,
    )
)
