"""Write specs for an artifact revision."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactRemoteStatus,
    ArtifactRevisionData,
    ArtifactStatus,
)
from ai.backend.manager.models.artifact_revision.creators import ArtifactRevisionCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import TestSeedFieldCreator


@dataclass(frozen=True)
class TestSeedArtifactRevision(TestSeedFieldCreator[ArtifactData, ArtifactRevisionData]):
    """One revision the artifact holds."""

    version: str = "1.0"
    status: ArtifactStatus = ArtifactStatus.SCANNED
    readme: str | None = "the revision readme"
    size: int | None = 1024
    remote_status: ArtifactRemoteStatus | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    digest: str | None = None
    verification_result: dict[str, Any] | None = None

    @override
    def kind(self) -> str:
        return Says(f"리비전 {self.version}", english=f"revision {self.version}")

    @override
    def owner_id(self, owner: ArtifactData) -> ArtifactID:
        return owner.id

    @override
    def seed(self) -> ArtifactRevisionCreator:
        return ArtifactRevisionCreator(
            version=self.version,
            readme=self.readme,
            size=self.size,
            status=self.status,
            remote_status=self.remote_status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            digest=self.digest,
            verification_result=self.verification_result,
        )
