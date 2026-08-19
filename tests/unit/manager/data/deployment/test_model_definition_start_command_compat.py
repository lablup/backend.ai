"""``start_command`` input compatibility (legacy list[str] → str).

Legacy ``start_command`` list inputs are converted with ``shlex.join``.
The new ``command`` field takes precedence and is stored internally as the
same single string.
"""

from __future__ import annotations

import textwrap
from typing import Any

import pytest
from ruamel.yaml import YAML
from sqlalchemy.engine.default import DefaultDialect

from ai.backend.common.config import (
    ModelDefinition,
    ModelServiceConfig,
    ModelServiceConfigDraft,
)
from ai.backend.manager.models.base import PydanticColumn

START_COMMAND_CASES = [
    pytest.param(
        "python service.py",
        None,
        "python service.py",
        id="string-no-shell",
    ),
    pytest.param(
        'python -c "import x; x.run()"',
        None,
        'python -c "import x; x.run()"',
        id="string-quoted-no-shell",
    ),
    pytest.param(
        "echo $HOME && exec python serve.py",
        "/bin/zsh",
        "echo $HOME && exec python serve.py",
        id="explicit-shell-custom",
    ),
    pytest.param(
        "python service.py --port 8080",
        "/bin/bash",
        "python service.py --port 8080",
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
    def test_str_input_is_preserved(self, raw: str, shell: str | None, expected: str) -> None:
        payload: dict[str, Any] = {"start_command": raw, "port": 8080}
        if shell is not None:
            payload["shell"] = shell
        draft = ModelServiceConfigDraft.model_validate(payload)
        assert draft.start_command == expected


class TestCommandFoldsIntoStartCommand:
    """``command`` supersedes the deprecated ``start_command``."""

    @pytest.mark.parametrize(("raw", "shell", "expected"), START_COMMAND_CASES)
    def test_command_is_resolved(self, raw: str, shell: str | None, expected: str) -> None:
        payload: dict[str, Any] = {"command": raw, "port": 8080}
        if shell is not None:
            payload["shell"] = shell
        resolved = ModelServiceConfig.model_validate(payload)
        assert resolved.start_command == expected

    @pytest.mark.parametrize(
        "start_command",
        [
            pytest.param("python old.py", id="str-start_command"),
            pytest.param(["python", "old.py"], id="list-start_command"),
        ],
    )
    def test_command_takes_precedence_over_start_command(
        self, start_command: str | list[str]
    ) -> None:
        resolved = ModelServiceConfig.model_validate({
            "command": "python new.py",
            "start_command": start_command,
            "port": 8080,
        })
        assert resolved.start_command == "python new.py"

    def test_command_is_not_persisted_as_extra(self) -> None:
        resolved = ModelServiceConfig.model_validate({
            "command": "python service.py",
            "port": 8080,
        })
        assert "command" not in resolved.model_dump()

    def test_hyphenated_start_command_alias_is_canonicalized(self) -> None:
        resolved = ModelServiceConfig.model_validate({
            "start-command": ["python", "old.py", "--flag", "a b"],
            "port": 8080,
        })
        assert resolved.start_command == "python old.py --flag 'a b'"
        dumped = resolved.model_dump()
        assert dumped["start_command"] == "python old.py --flag 'a b'"
        assert "start-command" not in dumped


class TestModelDefinitionInputCompat:
    """vfolder YAML scan → ``ModelDefinition.model_validate``."""

    @pytest.mark.parametrize(("raw", "shell", "expected"), START_COMMAND_CASES)
    def test_str_input_is_normalized(self, raw: str, shell: str | None, expected: str) -> None:
        result = ModelDefinition.model_validate(_wrap_definition(raw, shell))
        assert result.models[0].service is not None
        assert result.models[0].service.start_command == expected


class TestYAMLInputCompat:
    """End-to-end vfolder scan path: a user-authored ``model-definition.yaml``
    is parsed by ruamel.yaml and fed to ``ModelDefinition.model_validate``.
    Confirms that every YAML notation a user might write resolves to the same
    canonical command string.
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
                "python service.py",
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
                "echo $HOME | tee /tmp/out",
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
                "/bin/bash /models/start.sh",
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
                "/bin/bash /models/start.sh",
                id="block-sequence",
            ),
        ],
    )
    def test_yaml_forms_are_normalized(self, yaml_text: str, expected: str) -> None:
        loaded = YAML().load(yaml_text)
        result = ModelDefinition.model_validate(loaded)
        assert result.models[0].service is not None
        assert result.models[0].service.start_command == expected


class TestPydanticColumnReadCompat:
    """DB read path → ``PydanticColumn(ModelDefinition).process_result_value``."""

    @pytest.mark.parametrize(("raw", "shell", "expected"), START_COMMAND_CASES)
    def test_legacy_str_is_preserved(self, raw: str, shell: str | None, expected: str) -> None:
        column = PydanticColumn(ModelDefinition)
        resolved = column.process_result_value(_wrap_definition(raw, shell), DefaultDialect())
        assert resolved is not None
        assert resolved.models[0].service is not None
        assert resolved.models[0].service.start_command == expected
