"""Unit tests for ``start_command`` input compatibility (str → list[str]) in
``model_definition`` validators.

PR #11402 narrowed ``ModelServiceConfig.start_command`` from
``str | list[str]`` to ``list[str] | None``. To preserve backward
compatibility for users who still author the field as a shell string,
the validators normalize ``str`` input via :func:`shlex.split`.
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
        ["python", "service.py"],
        id="simple-split",
    ),
    pytest.param(
        'python -c "import x; x.run()"',
        ["python", "-c", "import x; x.run()"],
        id="shlex-preserves-quoted",
    ),
]


def _wrap_definition(start_command: str) -> dict[str, Any]:
    return {
        "models": [
            {
                "name": "model",
                "model_path": "/models/x",
                "service": {
                    "start_command": start_command,
                    "port": 8080,
                },
            }
        ]
    }


class TestPydanticInputCompat:
    """REST/GQL input → ``ModelServiceConfigDraft`` Pydantic validator."""

    @pytest.mark.parametrize(("raw", "expected"), START_COMMAND_CASES)
    def test_str_input_is_normalized(self, raw: str, expected: list[str]) -> None:
        draft = ModelServiceConfigDraft.model_validate({
            "start_command": raw,
            "port": 8080,
        })
        assert draft.start_command == expected


class TestTrafaretInputCompat:
    """vfolder YAML scan → ``model_definition_iv`` trafaret validator."""

    @pytest.mark.parametrize(("raw", "expected"), START_COMMAND_CASES)
    def test_str_input_is_normalized(self, raw: str, expected: list[str]) -> None:
        result = model_definition_iv.check(_wrap_definition(raw))
        assert result["models"][0]["service"]["start_command"] == expected


class TestYAMLInputCompat:
    """End-to-end vfolder scan path: a user-authored ``model-definition.yaml``
    is parsed by ruamel.yaml and fed to ``model_definition_iv``. Confirms that
    every YAML notation a user might write — legacy shell string, inline flow
    sequence, hyphenated block sequence — resolves to the same canonical
    ``list[str]``.
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
                ["python", "service.py"],
                id="legacy-shell-string",
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

    @pytest.mark.parametrize(("raw", "expected"), START_COMMAND_CASES)
    def test_legacy_str_is_normalized(self, raw: str, expected: list[str]) -> None:
        column = PydanticColumn(ModelDefinition)
        resolved = column.process_result_value(_wrap_definition(raw), DefaultDialect())
        assert resolved is not None
        assert resolved.models[0].service is not None
        assert resolved.models[0].service.start_command == expected
