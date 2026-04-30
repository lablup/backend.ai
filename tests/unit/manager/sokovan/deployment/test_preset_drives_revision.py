"""A preset that satisfies the required-field contract is enough on its
own — combined only with the per-deploy mount metadata the caller always
provides — to produce a fully populated ``ModelRevisionSpec`` via the
revision-draft merge chain. This is the invariant that lets
``model_card.deploy`` delegate every revision-shaping value to the
preset.
"""

from __future__ import annotations

import dataclasses
import functools
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode
from ai.backend.manager.data.deployment.types import MountMetadata, RevisionDraft
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    EnvironEntryData,
    ResourceOptsEntryData,
    ResourceSlotEntryData,
)
from ai.backend.manager.sokovan.deployment.revision_draft.reader import RevisionDraftReader


def _make_full_preset() -> DeploymentRevisionPresetData:
    return DeploymentRevisionPresetData(
        id=DeploymentPresetID(uuid.uuid4()),
        runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
        name="self-sufficient",
        description=None,
        rank=100,
        image_id=ImageID(uuid.uuid4()),
        model_definition=None,
        resource_opts=[ResourceOptsEntryData(name="shmem", value="1g")],
        cluster_mode="single-node",
        cluster_size=2,
        startup_command="python serve.py",
        bootstrap_script=None,
        environ=[EnvironEntryData(key="HF_HOME", value="/models/.cache")],
        preset_values=[],
        replica_count=3,
        deployment_strategy=DeploymentStrategy.ROLLING,
        deployment_strategy_spec={},
        open_to_public=None,
        revision_history_limit=None,
        created_at=datetime(2026, 4, 30, tzinfo=UTC),
        updated_at=None,
    )


async def test_preset_alone_resolves_to_model_revision_spec() -> None:
    preset = _make_full_preset()
    slot_entries = [
        ResourceSlotEntryData(resource_type="cpu", quantity="4"),
        ResourceSlotEntryData(resource_type="mem", quantity="8g"),
    ]

    reader = RevisionDraftReader(deployment_repository=MagicMock())
    preset_draft = reader._preset_to_draft(preset, slot_entries)
    # Caller leaves the request layer empty; model_card.deploy works this way.
    request_draft = RevisionDraft()
    merged = functools.reduce(RevisionDraft.merge, [preset_draft, request_draft], RevisionDraft())
    # ``runtime_variant_id`` does not flow through the draft chain (the
    # controller resolves it from the preset and uses it directly), so
    # mirror that step here before projecting to a spec.
    merged = dataclasses.replace(merged, runtime_variant_id=preset.runtime_variant_id)

    mounts = MountMetadata(
        model_vfolder_id=VFolderUUID(uuid.uuid4()),
        model_mount_destination="/models",
        model_definition_path="model-definition.yml",
        extra_mounts=[],
    )
    spec = merged.to_model_revision_spec(mounts)

    assert spec.image_id == preset.image_id
    assert spec.execution.runtime_variant_id == preset.runtime_variant_id
    assert spec.execution.startup_command == "python serve.py"
    assert spec.execution.environ == {"HF_HOME": "/models/.cache"}
    assert spec.resource_spec.cluster_mode == ClusterMode.SINGLE_NODE
    assert spec.resource_spec.cluster_size == 2
    assert spec.resource_spec.resource_slots == {"cpu": "4", "mem": "8g"}
    assert spec.mounts == mounts
