from __future__ import annotations

import shlex
from collections.abc import Mapping

from ai.backend.agent.errors.agent import InvalidArgumentError

__all__ = ("LegacyInferenceEnvTranslator",)


class LegacyInferenceEnvTranslator:
    """Translate legacy ``VLLM_*`` / ``SGLANG_*`` env vars into CLI args the baseline lost.

    Replaces the image ``start-*.sh`` wrapper the baseline ``start_command`` overrides.
    """

    # Env key -> CLI flag; value appended after the flag.
    _FLAG_BY_ENV: Mapping[str, str] = {
        "VLLM_QUANTIZATION": "--quantization",
        "VLLM_TP_SIZE": "--tensor-parallel-size",
        "VLLM_PP_SIZE": "--pipeline-parallel-size",
        "SGLANG_QUANTIZATION": "--quantization",
        "SGLANG_TP_SIZE": "--tensor-parallel-size",
        "SGLANG_PP_SIZE": "--pipeline-parallel-size",
    }

    # Raw arg-string keys: shell-split, appended last (override the flags above).
    _RAW_ARG_ENVS: tuple[str, ...] = ("VLLM_EXTRA_ARGS", "SGLANG_EXTRA_ARGS")

    @staticmethod
    def to_cli_args(environ: Mapping[str, str]) -> list[str]:
        args: list[str] = []
        for env_key, flag in LegacyInferenceEnvTranslator._FLAG_BY_ENV.items():
            value = environ.get(env_key)
            if value:
                args.append(flag)
                args.append(value)
        for env_key in LegacyInferenceEnvTranslator._RAW_ARG_ENVS:
            value = environ.get(env_key)
            if value:
                try:
                    args.extend(shlex.split(value))
                except ValueError as e:
                    raise InvalidArgumentError(f"Malformed quoting in {env_key}: {e}") from e
        return args
