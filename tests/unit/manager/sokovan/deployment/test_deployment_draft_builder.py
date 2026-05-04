from __future__ import annotations

from typing import cast
from unittest.mock import MagicMock

import pytest

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


def _revision_spec(model_definition: ModelDefinition | None) -> ModelRevisionSpec:
    revision = MagicMock(spec=ModelRevisionSpec)
    revision.model_definition = model_definition
    return cast(ModelRevisionSpec, revision)


def _context(args: list[str] | None) -> DeploymentContext:
    """Build a ``DeploymentContext`` with only the preset-args slice the
    builder method touches; everything else stays a ``MagicMock`` because
    ``_model_definition_payload`` does not read it."""
    context = MagicMock(spec=DeploymentContext)
    context.resolved_presets = (
        ResolvedPresetValues(environ={}, args=args) if args is not None else None
    )
    return cast(DeploymentContext, context)


class TestModelDefinitionPayload:
    """Tests scoped to the builder method only — the merge invariants
    themselves (identity on empty args, immutability, multi-model fan-out,
    ``service=None`` pass-through, ``start_command=None`` handling) are
    covered by ``TestModelDefinitionWithArgsAppended`` in
    ``tests/unit/common/test_config.py`` and not duplicated here.
    """

    @pytest.fixture
    def vllm_revision(self) -> ModelRevisionSpec:
        return _revision_spec(
            ModelDefinition(
                models=[
                    ModelConfig(
                        name="vllm-model",
                        model_path="/models",
                        service=ModelServiceConfig(
                            port=8000,
                            start_command=["vllm", "serve", "/models"],
                        ),
                    )
                ]
            )
        )

    async def test_returns_none_when_revision_has_no_definition(self) -> None:
        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            _revision_spec(None),
            _context(None),
        )

        assert payload is None

    @pytest.mark.parametrize(
        ("args", "expected_start_command"),
        [
            pytest.param(None, ["vllm", "serve", "/models"], id="presets-absent"),
            pytest.param([], ["vllm", "serve", "/models"], id="presets-empty"),
            pytest.param(
                ["--max-model-len", "4096"],
                ["vllm", "serve", "/models", "--max-model-len", "4096"],
                id="presets-with-args",
            ),
        ],
    )
    async def test_reads_args_from_context_into_dict_payload(
        self,
        vllm_revision: ModelRevisionSpec,
        args: list[str] | None,
        expected_start_command: list[str],
    ) -> None:
        # Builder wiring contract: pulls args from ``context.resolved_presets``
        # (handling both ``None`` and empty-list shapes) and returns a dict
        # ready for the kernel — i.e., ``model_dump`` has been called.
        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            vllm_revision, _context(args)
        )

        assert payload is not None
        assert isinstance(payload, dict)
        assert payload["models"][0]["service"]["start_command"] == expected_start_command

    async def test_args_tokenized_per_token_not_concatenated(
        self,
        vllm_revision: ModelRevisionSpec,
    ) -> None:
        # Regression guard for BA-5891 at the highest layer where the bug
        # surfaced: tokens must arrive split, so each value lands as its
        # own argv entry rather than ``"--port 8000"``. The same invariant
        # is implied by the parametrized expected lists above, but this
        # test makes it an explicit assertion at the kernel-payload boundary.
        tokens = ["--port", "8000", "--max-model-len", "4096"]

        payload = DeploymentSessionDraftBuilder._model_definition_payload(
            vllm_revision, _context(tokens)
        )

        assert payload is not None
        cmd = payload["models"][0]["service"]["start_command"]
        assert cmd == ["vllm", "serve", "/models", *tokens]
        assert all(" " not in token for token in cmd)
