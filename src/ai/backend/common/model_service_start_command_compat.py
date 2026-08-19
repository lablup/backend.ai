from __future__ import annotations

import shlex
from collections.abc import Mapping
from typing import Any

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


def to_legacy_start_command(command: str | None) -> list[str] | None:
    """Best-effort argv form of the internal command string for the deprecated
    ``start_command`` response field."""
    if command is None:
        return None
    try:
        return shlex.split(command)
    except ValueError:
        # Unparseable shell string (e.g. unclosed quote); keep it as a single argv item.
        return [command]
