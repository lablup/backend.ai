"""Unit tests for ``start_command`` input compatibility (str → list[str]) in
``model_definition`` validators.

PR #11402 narrowed ``ModelServiceConfig.start_command`` from
``str | list[str]`` to ``list[str] | None``. Legacy ``str`` inputs are
preserved by wrapping them as ``[shell, "-c", start_command]`` so the
original shell semantics (pipes, redirections, env expansion,
multiline) survive. ``shell`` falls back to ``/bin/bash`` when the
input omits it.
"""

from __future__ import annotations

import textwrap
from typing import Any

import pytest
from ruamel.yaml import YAML
from sqlalchemy.engine.default import DefaultDialect

from ai.backend.common.config import (
    ModelDefinition,
    ModelServiceConfigDraft,
    model_definition_iv,
)
from ai.backend.manager.models.base import PydanticColumn

START_COMMAND_CASES = [
    pytest.param(
        "python service.py",
        None,
        ["/bin/bash", "-c", "python service.py"],
        id="simple-default-shell",
    ),
    pytest.param(
        'python -c "import x; x.run()"',
        None,
        ["/bin/bash", "-c", 'python -c "import x; x.run()"'],
        id="quoted-default-shell",
    ),
    pytest.param(
        "echo $HOME && exec python serve.py",
        "/bin/zsh",
        ["/bin/zsh", "-c", "echo $HOME && exec python serve.py"],
        id="shell-semantics-custom-shell",
    ),
]


def _wrap_definition(start_command: str, shell: str | None = None) -> dict[str, Any]:
    service: dict[str, Any] = {
        "start_command": start_command,
        "port": 8080,
    }
    if shell is not None:
        service["shell"] = shell
    return {
        "models": [
            {
                "name": "model",
                "model_path": "/models/x",
                "service": service,
            }
        ]
    }


class TestPydanticInputCompat:
    """REST/GQL input → ``ModelServiceConfigDraft`` Pydantic validator."""

    @pytest.mark.parametrize(("raw", "shell", "expected"), START_COMMAND_CASES)
    def test_str_input_is_wrapped(self, raw: str, shell: str | None, expected: list[str]) -> None:
        payload: dict[str, Any] = {"start_command": raw, "port": 8080}
        if shell is not None:
            payload["shell"] = shell
        draft = ModelServiceConfigDraft.model_validate(payload)
        assert draft.start_command == expected


class TestTrafaretInputCompat:
    """vfolder YAML scan → ``model_definition_iv`` trafaret validator."""

    @pytest.mark.parametrize(("raw", "shell", "expected"), START_COMMAND_CASES)
    def test_str_input_is_wrapped(self, raw: str, shell: str | None, expected: list[str]) -> None:
        result = model_definition_iv.check(_wrap_definition(raw, shell))
        assert result["models"][0]["service"]["start_command"] == expected


class TestYAMLInputCompat:
    """End-to-end vfolder scan path: a user-authored ``model-definition.yaml``
    is parsed by ruamel.yaml and fed to ``model_definition_iv``. Confirms that
    every YAML notation a user might write — legacy shell string, inline flow
    sequence, hyphenated block sequence — resolves to the expected
    ``list[str]``. Legacy shell strings are wrapped via ``shell -c``; explicit
    argv lists pass through unchanged.
    """

    @pytest.mark.parametrize(
        ("yaml_text", "expected"),
        [
            pytest.param(
                textwrap.dedent("""\
                    models:
                    - name: model
                      model_path: /models/x
                      service:
                        start_command: python service.py
                        port: 8080
                """),
                ["/bin/bash", "-c", "python service.py"],
                id="legacy-shell-string-default-shell",
            ),
            pytest.param(
                textwrap.dedent("""\
                    models:
                    - name: model
                      model_path: /models/x
                      service:
                        start_command: echo $HOME | tee /tmp/out
                        shell: /bin/zsh
                        port: 8080
                """),
                ["/bin/zsh", "-c", "echo $HOME | tee /tmp/out"],
                id="legacy-shell-string-custom-shell",
            ),
            pytest.param(
                textwrap.dedent("""\
                    models:
                    - name: model
                      model_path: /models/x
                      service:
                        start_command: ["/bin/bash", "/models/start.sh"]
                        port: 8080
                """),
                ["/bin/bash", "/models/start.sh"],
                id="flow-sequence",
            ),
            pytest.param(
                textwrap.dedent("""\
                    models:
                    - name: model
                      model_path: /models/x
                      service:
                        start_command:
                        - /bin/bash
                        - /models/start.sh
                        port: 8080
                """),
                ["/bin/bash", "/models/start.sh"],
                id="block-sequence",
            ),
        ],
    )
    def test_yaml_forms_are_normalized(self, yaml_text: str, expected: list[str]) -> None:
        loaded = YAML().load(yaml_text)
        result = model_definition_iv.check(loaded)
        assert result["models"][0]["service"]["start_command"] == expected


class TestPydanticColumnReadCompat:
    """DB read path → ``PydanticColumn(ModelDefinition).process_result_value``.

    Downstream ``Row.to_data`` only forwards ``self.model_definition`` to the
    output dataclass, so verifying the resolved object here covers the
    read → to_data flow.
    """

    @pytest.mark.parametrize(("raw", "shell", "expected"), START_COMMAND_CASES)
    def test_legacy_str_is_wrapped(self, raw: str, shell: str | None, expected: list[str]) -> None:
        column = PydanticColumn(ModelDefinition)
        resolved = column.process_result_value(_wrap_definition(raw, shell), DefaultDialect())
        assert resolved is not None
        assert resolved.models[0].service is not None
        assert resolved.models[0].service.start_command == expected
