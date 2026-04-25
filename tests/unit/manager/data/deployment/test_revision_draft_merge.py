"""Unit tests for ``RevisionDraft.merge``."""

from __future__ import annotations

import functools
from uuid import uuid4

import yarl

from ai.backend.common.config import ModelConfigDraft, ModelDefinitionDraft
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.types import ClusterMode
from ai.backend.manager.data.deployment.types import RevisionDraft
from ai.backend.manager.data.deployment_revision_preset.types import PresetValueData


def _merge_all(*drafts: RevisionDraft) -> RevisionDraft:
    return functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())


class TestRevisionDraftMerge:
    def test_empty_merge_returns_empty(self) -> None:
        assert _merge_all() == RevisionDraft()

    def test_later_replaces_earlier_scalar_fields(self) -> None:
        image_a = ImageID(uuid4())
        image_b = ImageID(uuid4())
        variant_id = RuntimeVariantID(uuid4())
        earlier = RevisionDraft(
            image_id=image_a,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            startup_command="echo a",
            runtime_variant_id=variant_id,
            callback_url=yarl.URL("http://a"),
        )
        later = RevisionDraft(
            image_id=image_b,
            cluster_size=2,
            startup_command="echo b",
            callback_url=yarl.URL("http://b"),
        )
        merged = earlier.merge(later)
        assert merged.image_id == image_b
        assert merged.cluster_mode == ClusterMode.SINGLE_NODE  # earlier preserved
        assert merged.cluster_size == 2
        assert merged.startup_command == "echo b"
        assert merged.runtime_variant_id == variant_id
        assert merged.callback_url == yarl.URL("http://b")

    def test_none_in_later_does_not_override(self) -> None:
        earlier = RevisionDraft(cluster_size=4, startup_command="echo a")
        later = RevisionDraft()  # all None
        merged = earlier.merge(later)
        assert merged.cluster_size == 4
        assert merged.startup_command == "echo a"

    def test_environ_dict_merge(self) -> None:
        earlier = RevisionDraft(environ={"A": "1", "B": "2"})
        middle = RevisionDraft(environ={"B": "3", "C": "4"})
        later = RevisionDraft(environ={"C": "5"})
        merged = _merge_all(earlier, middle, later)
        assert merged.environ == {"A": "1", "B": "3", "C": "5"}

    def test_resource_slots_dict_merge(self) -> None:
        earlier = RevisionDraft(resource_slots={"cpu": "1", "mem": "1g"})
        later = RevisionDraft(resource_slots={"cpu": "4"})
        merged = earlier.merge(later)
        assert merged.resource_slots == {"cpu": "4", "mem": "1g"}

    def test_resource_opts_dict_merge(self) -> None:
        earlier = RevisionDraft(resource_opts={"shmem": "1g"})
        later = RevisionDraft(resource_opts={"shmem": "2g", "extra": "v"})
        merged = earlier.merge(later)
        assert merged.resource_opts == {"shmem": "2g", "extra": "v"}

    def test_model_definition_uses_merge_when_both_present(self) -> None:
        base = ModelDefinitionDraft(
            models=[ModelConfigDraft(name="m-base", model_path="/models/base")]
        )
        override = ModelDefinitionDraft(
            models=[ModelConfigDraft(name="m-override", model_path="/models/override")]
        )
        earlier = RevisionDraft(model_definition=base)
        later = RevisionDraft(model_definition=override)
        merged = earlier.merge(later)
        assert merged.model_definition is not None
        assert merged.model_definition.models is not None
        # Merge uses per-index merge of ModelConfigDraft (model name is replaced).
        assert merged.model_definition.models[0].name == "m-override"

    def test_model_definition_replaced_when_earlier_missing(self) -> None:
        override = ModelDefinitionDraft(models=[ModelConfigDraft(name="m", model_path="/models/m")])
        earlier = RevisionDraft()
        later = RevisionDraft(model_definition=override)
        merged = earlier.merge(later)
        assert merged.model_definition is override

    def test_preset_values_replaced_by_latest_non_none(self) -> None:
        first = [PresetValueData(preset_id=DeploymentPresetID(uuid4()), value="a")]
        second = [PresetValueData(preset_id=DeploymentPresetID(uuid4()), value="b")]
        earlier = RevisionDraft(preset_values=first)
        later = RevisionDraft(preset_values=second)
        merged = earlier.merge(later)
        assert merged.preset_values == second
