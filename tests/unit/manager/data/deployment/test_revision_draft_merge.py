"""Unit tests for RevisionDraft + merge_revision_drafts."""

from __future__ import annotations

from uuid import uuid4

import yarl

from ai.backend.common.config import ModelConfigDraft, ModelDefinitionDraft
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    RevisionDraft,
    merge_revision_drafts,
)
from ai.backend.manager.data.deployment_revision_preset.types import PresetValueData


class TestMergeRevisionDrafts:
    def test_empty_merge_returns_empty(self) -> None:
        assert merge_revision_drafts() == RevisionDraft()

    def test_later_replaces_earlier_scalar_fields(self) -> None:
        earlier = RevisionDraft(
            image_canonical="img:a",
            image_architecture="x86_64",
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            startup_command="echo a",
            runtime_variant=RuntimeVariant("vllm"),
            callback_url=yarl.URL("http://a"),
        )
        later = RevisionDraft(
            image_canonical="img:b",
            cluster_size=2,
            startup_command="echo b",
            callback_url=yarl.URL("http://b"),
        )
        merged = merge_revision_drafts(earlier, later)
        assert merged.image_canonical == "img:b"
        assert merged.image_architecture == "x86_64"  # earlier preserved
        assert merged.cluster_mode == ClusterMode.SINGLE_NODE  # earlier preserved
        assert merged.cluster_size == 2
        assert merged.startup_command == "echo b"
        assert merged.runtime_variant == RuntimeVariant("vllm")
        assert merged.callback_url == yarl.URL("http://b")

    def test_none_in_later_does_not_override(self) -> None:
        earlier = RevisionDraft(cluster_size=4, startup_command="echo a")
        later = RevisionDraft()  # all None
        merged = merge_revision_drafts(earlier, later)
        assert merged.cluster_size == 4
        assert merged.startup_command == "echo a"

    def test_environ_dict_merge(self) -> None:
        earlier = RevisionDraft(environ={"A": "1", "B": "2"})
        middle = RevisionDraft(environ={"B": "3", "C": "4"})
        later = RevisionDraft(environ={"C": "5"})
        merged = merge_revision_drafts(earlier, middle, later)
        assert merged.environ == {"A": "1", "B": "3", "C": "5"}

    def test_resource_slots_dict_merge(self) -> None:
        earlier = RevisionDraft(resource_slots={"cpu": "1", "mem": "1g"})
        later = RevisionDraft(resource_slots={"cpu": "4"})
        merged = merge_revision_drafts(earlier, later)
        assert merged.resource_slots == {"cpu": "4", "mem": "1g"}

    def test_resource_opts_dict_merge(self) -> None:
        earlier = RevisionDraft(resource_opts={"shmem": "1g"})
        later = RevisionDraft(resource_opts={"shmem": "2g", "extra": "v"})
        merged = merge_revision_drafts(earlier, later)
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
        merged = merge_revision_drafts(earlier, later)
        assert merged.model_definition is not None
        assert merged.model_definition.models is not None
        # Merge uses per-index merge of ModelConfigDraft (model name is replaced).
        assert merged.model_definition.models[0].name == "m-override"

    def test_model_definition_replaced_when_earlier_missing(self) -> None:
        override = ModelDefinitionDraft(models=[ModelConfigDraft(name="m", model_path="/models/m")])
        earlier = RevisionDraft()
        later = RevisionDraft(model_definition=override)
        merged = merge_revision_drafts(earlier, later)
        assert merged.model_definition is override

    def test_preset_values_replaced_by_latest_non_none(self) -> None:
        first = [PresetValueData(preset_id=uuid4(), value="a")]
        second = [PresetValueData(preset_id=uuid4(), value="b")]
        earlier = RevisionDraft(preset_values=first)
        later = RevisionDraft(preset_values=second)
        merged = merge_revision_drafts(earlier, later)
        assert merged.preset_values == second
