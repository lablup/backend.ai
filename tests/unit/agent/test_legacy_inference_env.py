from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.legacy_inference_env import LegacyInferenceEnvTranslator
from ai.backend.common.config import ModelConfig


@dataclass(frozen=True)
class CollectScenario:
    id: str
    environ: dict[str, str]
    expected: list[str]


class TestLegacyInferenceEnvTranslatorToCliArgs:
    @pytest.mark.parametrize(
        "scenario",
        [
            CollectScenario(id="empty_environ", environ={}, expected=[]),
            CollectScenario(
                id="ignores_unknown_keys",
                environ={"PATH": "/usr/bin", "VLLM_VERSION": "0.9.1"},
                expected=[],
            ),
            CollectScenario(
                id="skips_empty_values",
                environ={"VLLM_TP_SIZE": "", "VLLM_EXTRA_ARGS": ""},
                expected=[],
            ),
            CollectScenario(
                id="maps_flag_envs_with_values",
                environ={
                    "VLLM_QUANTIZATION": "awq",
                    "VLLM_TP_SIZE": "4",
                    "VLLM_PP_SIZE": "2",
                },
                expected=[
                    "--quantization",
                    "awq",
                    "--tensor-parallel-size",
                    "4",
                    "--pipeline-parallel-size",
                    "2",
                ],
            ),
            CollectScenario(
                id="shlex_splits_extra_args",
                environ={"VLLM_EXTRA_ARGS": "--trust-remote-code --max-model-len 524288"},
                expected=["--trust-remote-code", "--max-model-len", "524288"],
            ),
            CollectScenario(
                id="extra_args_appended_after_flag_envs",
                environ={
                    "VLLM_TP_SIZE": "4",
                    "VLLM_EXTRA_ARGS": "--trust-remote-code --reasoning-parser kimi_k2",
                },
                expected=[
                    "--tensor-parallel-size",
                    "4",
                    "--trust-remote-code",
                    "--reasoning-parser",
                    "kimi_k2",
                ],
            ),
            CollectScenario(
                id="shlex_respects_quotes",
                environ={"VLLM_EXTRA_ARGS": "--foo 'a b' --bar"},
                expected=["--foo", "a b", "--bar"],
            ),
            CollectScenario(
                id="maps_sglang_envs",
                environ={
                    "SGLANG_TP_SIZE": "8",
                    "SGLANG_EXTRA_ARGS": "--trust-remote-code",
                },
                expected=["--tensor-parallel-size", "8", "--trust-remote-code"],
            ),
            CollectScenario(
                id="keeps_quoted_json_arg_as_single_token",
                environ={
                    "VLLM_EXTRA_ARGS": (
                        '--hf-overrides \'{"rope_parameters": {"type": "yarn",'
                        ' "factor": 4.0}}\' --max-model-len 524288'
                    ),
                },
                expected=[
                    "--hf-overrides",
                    '{"rope_parameters": {"type": "yarn", "factor": 4.0}}',
                    "--max-model-len",
                    "524288",
                ],
            ),
            CollectScenario(
                id="preserves_key_value_and_dotted_tokens",
                environ={
                    "VLLM_EXTRA_ARGS": (
                        "--attention-config.use_trtllm_ragged_deepseek_prefill=True"
                        " --hf-overrides.rope_parameters.factor 2.0"
                    ),
                },
                expected=[
                    "--attention-config.use_trtllm_ragged_deepseek_prefill=True",
                    "--hf-overrides.rope_parameters.factor",
                    "2.0",
                ],
            ),
        ],
        ids=lambda scenario: scenario.id,
    )
    def test_to_cli_args(
        self,
        scenario: CollectScenario,
    ) -> None:
        assert LegacyInferenceEnvTranslator.to_cli_args(scenario.environ) == scenario.expected


def _model(name: str, start_command: list[str] | None) -> ModelConfig:
    return ModelConfig.model_validate({
        "name": name,
        "model_path": f"/models/{name}",
        "service": {
            "port": 8000,
            "shell": "/bin/bash",
            "start_command": start_command,
        },
    })


class TestAppendLegacyInferenceEnvTranslator:
    def test_appends_to_existing_start_command(self) -> None:
        models = [_model("vllm", ["vllm", "serve", "/models"])]
        environ = {"VLLM_EXTRA_ARGS": "--trust-remote-code", "VLLM_TP_SIZE": "4"}

        result = AbstractAgent._append_legacy_inference_env_args(
            cast(AbstractAgent[Any, Any], object()),
            models,
            environ,
        )

        assert result is models
        service = models[0].service
        assert service is not None
        assert service.start_command == [
            "vllm",
            "serve",
            "/models",
            "--tensor-parallel-size",
            "4",
            "--trust-remote-code",
        ]

    def test_noop_without_legacy_env(self) -> None:
        models = [_model("vllm", ["vllm", "serve", "/models"])]

        AbstractAgent._append_legacy_inference_env_args(
            cast(AbstractAgent[Any, Any], object()),
            models,
            {"PATH": "/usr/bin"},
        )

        service = models[0].service
        assert service is not None
        assert service.start_command == ["vllm", "serve", "/models"]

    def test_skips_model_without_service(self) -> None:
        models = [
            ModelConfig.model_validate({"name": "no-service", "model_path": "/models/x"}),
            _model("vllm", ["vllm", "serve", "/models"]),
        ]

        AbstractAgent._append_legacy_inference_env_args(
            cast(AbstractAgent[Any, Any], object()),
            models,
            {"VLLM_EXTRA_ARGS": "--trust-remote-code"},
        )

        assert models[0].service is None
        service = models[1].service
        assert service is not None
        assert service.start_command == ["vllm", "serve", "/models", "--trust-remote-code"]
