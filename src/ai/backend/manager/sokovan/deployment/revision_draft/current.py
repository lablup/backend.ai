"""Convert the current ModelRevisionData into a RevisionDraft for use as the
lowest-priority base when building a successor revision (e.g. on modify).

Only fields that live on ``ModelRevisionData`` can be carried over. Fields
that are not part of that data structure (startup_command, bootstrap_script,
callback_url) remain ``None`` — the pipeline is expected to resolve them from
``deployment-config.yaml``, preset, ``model-definition.yaml``, or the user
overrides, exactly as during fresh creation.
"""

from __future__ import annotations

from ai.backend.manager.data.deployment.types import ModelRevisionData, RevisionDraft


def revision_draft_from_current(current: ModelRevisionData) -> RevisionDraft:
    environ = current.model_runtime_config.environ
    resource_slots = dict(current.resource_config.resource_slot) or None
    resource_opts = dict(current.resource_config.resource_opts) or None
    return RevisionDraft(
        image_id=current.image_id,
        resource_slots=resource_slots,
        resource_opts=resource_opts,
        cluster_mode=current.cluster_config.mode,
        cluster_size=current.cluster_config.size,
        environ={k: str(v) for k, v in environ.items()} if environ else None,
        runtime_variant=current.model_runtime_config.runtime_variant,
        inference_runtime_config=current.model_runtime_config.inference_runtime_config,
        model_definition=current.model_definition,
    )
