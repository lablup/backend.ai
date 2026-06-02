"""Unit tests for ``RevisionDraftReader``."""

from __future__ import annotations

import functools
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from ai.backend.common.config import ModelConfigDraft, ModelDefinitionDraft
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.deployment.types import (
    FetchedModelDefinition,
    MountMetadata,
    RevisionDraft,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.sokovan.deployment.revision_draft.reader import RevisionDraftReader


def _reader() -> RevisionDraftReader:
    return RevisionDraftReader(deployment_repository=cast(Any, object()))


def _mounts(model_mount_destination: str = "/models") -> MountMetadata:
    return MountMetadata(
        model_vfolder_id=VFolderUUID(uuid4()),
        model_definition_path=None,
        model_mount_destination=model_mount_destination,
        extra_mounts=[],
    )


def _variant(reads_vfolder_config_files: bool = False) -> RuntimeVariantData:
    return RuntimeVariantData(
        id=RuntimeVariantID(uuid4()),
        name="custom",
        description=None,
        reads_vfolder_config_files=reads_vfolder_config_files,
        default_model_definition=ModelDefinitionDraft(),
        created_at=datetime(2026, 5, 15, tzinfo=UTC),
        updated_at=None,
    )


def _merge_all(*drafts: RevisionDraft) -> RevisionDraft:
    return functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())


class TestRevisionDraftReaderModelPathDefault:
    def test_adds_lowest_priority_model_path_default(self) -> None:
        drafts = [
            _reader()._model_mount_path_default_draft(_mounts("/mnt/models")),
            RevisionDraft(
                model_definition=ModelDefinitionDraft(models=[ModelConfigDraft(name="base")])
            ),
            RevisionDraft(
                model_definition=ModelDefinitionDraft(
                    models=[
                        ModelConfigDraft(name="override-0"),
                    ]
                )
            ),
        ]

        merged = _merge_all(*drafts)

        assert merged.model_definition is not None
        assert merged.model_definition.models is not None
        assert merged.model_definition.models[0].name == "override-0"
        assert merged.model_definition.models[0].model_path == "/mnt/models"


class TestRevisionDraftReaderVFolderDrafts:
    async def test_records_resolved_default_model_definition_path(self) -> None:
        repository = MagicMock()
        repository.fetch_deployment_config = AsyncMock(return_value=None)
        repository.fetch_model_definition = AsyncMock(
            return_value=FetchedModelDefinition(
                path="model-definition.yml",
                model_definition=ModelDefinitionDraft(models=[ModelConfigDraft(name="from-file")]),
            )
        )
        reader = RevisionDraftReader(deployment_repository=repository)
        variant = _variant(reads_vfolder_config_files=True)

        drafts = await reader._read_vfolder_drafts(_mounts(), variant)
        merged = _merge_all(*drafts)

        assert merged.mounts is not None
        assert merged.mounts.model_definition_path == "model-definition.yml"
        assert merged.model_definition is not None
        assert merged.model_definition.models is not None
        assert merged.model_definition.models[0].name == "from-file"
