"""``start_command`` input compatibility (str → list[str]).

PR #11402 narrowed ``start_command`` to ``list[str] | None``. Legacy
``str`` inputs are wrapped as ``[shell, "-c", str]`` only when the user
sets ``shell``; otherwise they pass through as ``[str]`` so shell-less
images stay launchable.
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
)
from ai.backend.manager.models.base import PydanticColumn

START_COMMAND_CASES = [
    pytest.param(
        "python service.py",
        None,
        ["python service.py"],
        id="no-shell-single-argv",
    ),
    pytest.param(
        'python -c "import x; x.run()"',
        None,
        ['python -c "import x; x.run()"'],
        id="no-shell-quoted-single-argv",
    ),
    pytest.param(
        "echo $HOME && exec python serve.py",
        "/bin/zsh",
        ["/bin/zsh", "-c", "echo $HOME && exec python serve.py"],
        id="explicit-shell-custom",
    ),
    pytest.param(
        "python service.py --port 8080",
        "/bin/bash",
        ["/bin/bash", "-c", "python service.py --port 8080"],
        id="explicit-shell-bash",
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


class TestModelDefinitionInputCompat:
    """vfolder YAML scan → ``ModelDefinition.model_validate``."""

    @pytest.mark.parametrize(("raw", "expected"), START_COMMAND_CASES)
    def test_str_input_is_normalized(self, raw: str, expected: list[str]) -> None:
        result = ModelDefinition.model_validate(_wrap_definition(raw))
        assert result.models[0].service is not None
        assert result.models[0].service.start_command == expected


class TestYAMLInputCompat:
    """End-to-end vfolder scan path: a user-authored ``model-definition.yaml``
    is parsed by ruamel.yaml and fed to ``ModelDefinition.model_validate``.
    Confirms that every YAML notation a user might write — legacy shell string,
    inline flow sequence, hyphenated block sequence — resolves to the same
    canonical ``list[str]``.
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
                ["python service.py"],
                id="legacy-shell-string-no-shell-key",
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
                id="legacy-shell-string-explicit-shell",
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
        result = ModelDefinition.model_validate(loaded)
        assert result.models[0].service is not None
        assert result.models[0].service.start_command == expected


class TestPydanticColumnReadCompat:
    """DB read path → ``PydanticColumn(ModelDefinition).process_result_value``."""

    @pytest.mark.parametrize(("raw", "shell", "expected"), START_COMMAND_CASES)
    def test_legacy_str_is_wrapped(self, raw: str, shell: str | None, expected: list[str]) -> None:
        column = PydanticColumn(ModelDefinition)
        resolved = column.process_result_value(_wrap_definition(raw, shell), DefaultDialect())
        assert resolved is not None
        assert resolved.models[0].service is not None
        assert resolved.models[0].service.start_command == expected
