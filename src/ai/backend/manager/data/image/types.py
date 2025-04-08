import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Self

from ai.backend.common.types import AutoScalingMetricComparator, AutoScalingMetricSource
from ai.backend.manager.models.image import ImageRow, ImageStatus, ImageType


@dataclass
class ImageLabelsData:
    label_data: dict[str, str]


@dataclass
class ImageResourcesData:
    resources_data: dict[str, dict[str, Optional[str]]]


@dataclass
class ImageData:
    id: uuid.UUID
    name: str
    project: Optional[str]
    image: str
    created_at: Optional[datetime]
    tag: Optional[str]
    registry: str
    registry_id: uuid.UUID
    architecture: str
    config_digest: str
    size_bytes: int
    is_local: bool
    type: ImageType
    accelerators: Optional[str]
    labels: ImageLabelsData
    resources: ImageResourcesData
    status: ImageStatus

    @classmethod
    def from_row(cls, row: Optional[ImageRow]) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            name=row.name,
            project=row.project,
            image=row.image,
            created_at=row.created_at,
            tag=row.tag,
            registry=row.registry,
            registry_id=row.registry_id,
            architecture=row.architecture,
            config_digest=row.config_digest,
            size_bytes=row.size_bytes,
            is_local=row.is_local,
            type=row.type,
            accelerators=row.accelerators,
            labels=ImageLabelsData(label_data=row.labels),
            resources=ImageResourcesData(resources_data=row.resources),
            status=row.status,
        )


@dataclass
class RescanImagesResult:
    images: list[ImageData]
    errors: list[str] = field(default_factory=list)


@dataclass
class ImageAliasData:
    id: uuid.UUID
    alias: str


@dataclass
class EndpointAutoScalingRuleData:
    id: uuid.UUID
    metric_source: AutoScalingMetricSource
    metric_name: str
    threshold: str
    comparator: AutoScalingMetricComparator
    step_size: int
    cooldown_seconds: int
    min_replicas: int
    max_replicas: int
    created_at: datetime
    last_triggered_at: datetime
    endpoint: uuid.UUID

    @classmethod
    def from_row(cls, row) -> Optional[Self]:
        if row is None:
            return None
        return cls(
            id=row.id,
            metric_source=row.metric_source,
            metric_name=row.metric_name,
            threshold=row.threshold,
            comparator=row.comparator,
            step_size=row.step_size,
            cooldown_seconds=row.cooldown_seconds,
            min_replicas=row.min_replicas,
            max_replicas=row.max_replicas,
            created_at=row.created_at,
            last_triggered_at=row.last_triggered_at,
            endpoint=row.endpoint,
        )
