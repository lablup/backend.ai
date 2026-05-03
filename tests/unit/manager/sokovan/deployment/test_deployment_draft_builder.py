"""Unit tests for ``DeploymentSessionDraftBuilder`` helpers.

The builder appends ``ResolvedPresetValues.args`` onto each model's
``service.start_command`` as separate argv tokens. Resolution of
``{model_path}`` placeholders happens earlier (at
``ModelConfigDraft.to_resolved`` during revision creation), so the
snapshot the builder reads here already carries fully-resolved argv.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelServiceConfig,
)
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    DeploymentContext,
    ResolvedPresetValues,
)
from ai.backend.manager.sokovan.deployment.deployment_draft_builder import (
    DeploymentSessionDraftBuilder,
)


def _model_definition(start_command: list[str] | None) -> ModelDefinition:
    return ModelDefinition(
        models=[
            ModelConfig(
                name="vllm-model",
                model_path="/models",
                service=ModelServiceConfig(
                    port=8000,
                    start_command=start_command,
                ),
            )
        ]
    )


def _revision_spec(model_definition: ModelDefinition | None) -> ModelRevisionSpec:
    revision = MagicMock(spec=ModelRevisionSpec)
    revision.model_definition = model_definition
    return cast(ModelRevisionSpec, revision)


def _context(args: list[str] | None) -> DeploymentContext:
    context = MagicMock(spec=DeploymentContext)
    context.resolved_presets = (
        ResolvedPresetValues(environ={}, args=list(args)) if args is not None else None
    )
    return cast(DeploymentContext, context)


class TestModelDefinitionPayload:
    """``_model_definition_payload`` appends preset ARGS onto the snapshot
    ``service.start_command`` as separate argv tokens. Without args it is
    a pass-through ``model_dump`` of the resolved ``ModelDefinition``."""

    def test_returns_none_when_revision_has_no_definition(self) -> None:
        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            _revision_spec(None),
            _context(None),
        )

        assert payload is None

    def test_no_presets_passes_through_unchanged(self) -> None:
        revision = _revision_spec(_model_definition(start_command=["vllm", "serve", "/models"]))

        payload = DeploymentSessionDraftBuilder._model_definition_payload(revision, _context(None))

        assert payload is not None
        assert payload["models"][0]["service"]["start_command"] == [
            "vllm",
            "serve",
            "/models",
        ]

    def test_appends_args_to_existing_start_command(self) -> None:
        revision = _revision_spec(_model_definition(start_command=["vllm", "serve", "/models"]))

        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            revision, _context(["--max-model-len", "4096"])
        )

        assert payload is not None
        assert payload["models"][0]["service"]["start_command"] == [
            "vllm",
            "serve",
            "/models",
            "--max-model-len",
            "4096",
        ]

    def test_args_become_start_command_when_definition_has_none(self) -> None:
        # Snapshot with no start_command (e.g. cmd/custom variants) still
        # accepts preset args, but the agent's image-CMD fallback has to
        # provide the launcher prefix.
        revision = _revision_spec(_model_definition(start_command=None))

        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            revision, _context(["--port", "8000"])
        )

        assert payload is not None
        assert payload["models"][0]["service"]["start_command"] == ["--port", "8000"]

    def test_empty_args_leaves_start_command_unchanged(self) -> None:
        revision = _revision_spec(_model_definition(start_command=["vllm", "serve", "/models"]))

        payload = DeploymentSessionDraftBuilder._model_definition_payload(revision, _context([]))

        assert payload is not None
        assert payload["models"][0]["service"]["start_command"] == [
            "vllm",
            "serve",
            "/models",
        ]

    def test_args_tokenized_per_token_not_concatenated(self) -> None:
        # Regression guard for BA-5891: tokens must arrive split, so each
        # value lands as its own argv entry rather than ``"--port 8000"``.
        revision = _revision_spec(_model_definition(start_command=["vllm", "serve", "/models"]))
        tokens = ["--port", "8000", "--max-model-len", "4096"]

        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            revision, _context(tokens)
        )

        assert payload is not None
        cmd = payload["models"][0]["service"]["start_command"]
        assert cmd == ["vllm", "serve", "/models", *tokens]
        assert all(" " not in token for token in cmd)

    def test_each_model_in_payload_receives_args(self) -> None:
        # Multi-model definitions are rare but supported; the merge applies
        # to every entry uniformly.
        definition = ModelDefinition(
            models=[
                ModelConfig(
                    name="model-a",
                    model_path="/models/a",
                    service=ModelServiceConfig(port=8001, start_command=["a"]),
                ),
                ModelConfig(
                    name="model-b",
                    model_path="/models/b",
                    service=ModelServiceConfig(port=8002, start_command=["b"]),
                ),
            ]
        )
        revision = _revision_spec(definition)

        payload = cast(
            dict[str, Any],
            DeploymentSessionDraftBuilder._model_definition_payload(
                revision, _context(["--shared", "true"])
            ),
        )

        assert payload["models"][0]["service"]["start_command"] == [
            "a",
            "--shared",
            "true",
        ]
        assert payload["models"][1]["service"]["start_command"] == [
            "b",
            "--shared",
            "true",
        ]
