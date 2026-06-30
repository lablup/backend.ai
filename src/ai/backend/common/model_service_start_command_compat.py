from __future__ import annotations

import shlex
from collections.abc import Mapping
from typing import Any, cast

MODEL_SERVICE_COMMAND_KEYS = frozenset(("command", "start_command", "start-command"))


def resolve_model_service_start_command(service: Any) -> Any:
    if not isinstance(service, Mapping):
        return service
    return _normalize_model_service_command_input(service)


def _normalize_model_service_command_input(service: Mapping[str, Any]) -> dict[str, Any]:
    result = {k: v for k, v in service.items() if k not in MODEL_SERVICE_COMMAND_KEYS}
    command = service.get("command")
    if command is None:
        command = service.get("start_command", service.get("start-command"))
        if isinstance(command, list) and all(isinstance(item, str) for item in command):
            command = shlex.join(command)
    if command is not None or "start_command" in service or "start-command" in service:
        result["start_command"] = command
    return result


def normalize_model_service_command_response(service: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(service)
    command = result.get("command")
    if command is None:
        command = result.get("start_command")
        if isinstance(command, list) and all(isinstance(item, str) for item in command):
            command = shlex.join(command)

    if command is None:
        result["start_command"] = None
    else:
        try:
            result["start_command"] = shlex.split(cast(str, command))
        except ValueError:
            result["start_command"] = [command]
    result["command"] = command
    return result
