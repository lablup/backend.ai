"""Unit tests for ``RevisionDraftReader``."""

from __future__ import annotations

import functools
from typing import Any, cast
from uuid import uuid4

from ai.backend.common.config import ModelConfigDraft, ModelDefinitionDraft
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.deployment.types import MountMetadata, RevisionDraft
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
