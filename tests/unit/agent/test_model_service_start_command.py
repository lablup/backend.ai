from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, cast

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.common.config import ModelConfig

TEST_IMAGE = "example.com/custom-vllm:latest"


@dataclass(frozen=True)
class ModelServiceStartCommandScenario:
    id: str
    image_command: list[str] | None
    models: list[ModelConfig]
    expected_start_commands: dict[str, str]
    expected_image_command_calls: int = 1
    expected_unset_models: set[str] = field(default_factory=set)


class _ModelServiceCommandAgent:
    def __init__(
        self,
        image_command: list[str] | None,
        *,
        raise_not_implemented: bool = False,
    ) -> None:
        self.calls: list[str] = []
        self._image_command = image_command
        self._raise_not_implemented = raise_not_implemented

    async def extract_image_command(self, image: str) -> list[str] | None:
        self.calls.append(image)
        if self._raise_not_implemented:
            raise NotImplementedError
        return self._image_command


def _model(
    name: str,
    port: int,
    start_command: str | None = None,
    shell: str = "/bin/bash",
) -> ModelConfig:
    return ModelConfig.model_validate({
        "name": name,
        "model_path": f"/models/{name}",
        "service": {
            "port": port,
            "shell": shell,
            "start_command": start_command if start_command is not None else None,
        },
    })


class TestPopulateMissingModelServiceStartCommands:
    @pytest.fixture
    def image(self) -> str:
        return TEST_IMAGE

    @pytest.fixture
    def agent(
        self,
        scenario: ModelServiceStartCommandScenario,
    ) -> _ModelServiceCommandAgent:
        return _ModelServiceCommandAgent(scenario.image_command)

    @pytest.fixture
    def models(
        self,
        scenario: ModelServiceStartCommandScenario,
    ) -> list[ModelConfig]:
        return deepcopy(scenario.models)

    @pytest.mark.parametrize(
        "scenario",
        [
            ModelServiceStartCommandScenario(
                id="uses_list_command_from_image",
                image_command=["/etc/container/start-vllm.sh"],
                models=[
                    _model("vllm", 8000),
                    _model("explicit", 8001, "python serve.py"),
                ],
                expected_start_commands={
                    "vllm": "/etc/container/start-vllm.sh",
                    "explicit": "python serve.py",
                },
            ),
            ModelServiceStartCommandScenario(
                id="leaves_missing_command_unset_without_image_command",
                image_command=None,
                models=[
                    _model("vllm", 8000),
                ],
                expected_start_commands={},
                expected_unset_models={"vllm"},
            ),
            ModelServiceStartCommandScenario(
                id="skips_image_command_lookup_when_all_commands_are_explicit",
                image_command=["/etc/container/start-vllm.sh"],
                models=[
                    _model("explicit-a", 8000, "python serve-a.py"),
                    _model("explicit-b", 8001, "python serve-b.py"),
                ],
                expected_start_commands={
                    "explicit-a": "python serve-a.py",
                    "explicit-b": "python serve-b.py",
                },
                expected_image_command_calls=0,
            ),
        ],
        ids=lambda scenario: scenario.id,
    )
    async def test_populates_missing_commands_from_image_command(
        self,
        scenario: ModelServiceStartCommandScenario,
        agent: _ModelServiceCommandAgent,
        models: list[ModelConfig],
        image: str,
    ) -> None:
        populated_models = await AbstractAgent._apply_image_cmd_fallback(
            cast(AbstractAgent[Any, Any], agent),
            models,
            image,
        )

        assert populated_models is models
        assert agent.calls == [image] * scenario.expected_image_command_calls
        services = {model.name: model.service for model in populated_models}
        for model_name, expected_start_command in scenario.expected_start_commands.items():
            service = services[model_name]
            assert service is not None
            assert service.start_command == expected_start_command
        for model_name in scenario.expected_unset_models:
            service = services[model_name]
            assert service is not None
            assert not service.start_command

    @pytest.fixture
    def raise_not_implemented_agent(
        self,
    ) -> _ModelServiceCommandAgent:
        return _ModelServiceCommandAgent(None, raise_not_implemented=True)

    async def test_reraises_not_implemented_error(
        self,
        image: str,
        raise_not_implemented_agent: _ModelServiceCommandAgent,
    ) -> None:
        models = [_model("vllm", 8000)]

        with pytest.raises(NotImplementedError):
            await AbstractAgent._apply_image_cmd_fallback(
                cast(AbstractAgent[Any, Any], raise_not_implemented_agent),
                models,
                image,
            )

        assert raise_not_implemented_agent.calls == [image]
        assert models[0].service is not None
        assert not models[0].service.start_command
