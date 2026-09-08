"""Request-DTO "unset" markers never reach the GraphQL schema as input defaults."""

from __future__ import annotations

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.tristate.unset import Unset
from ai.backend.manager.api.gql.schema import schema


def _input_defaults() -> list[tuple[str, str, object]]:
    found: list[tuple[str, str, object]] = []
    for type_name, type_def in schema._schema.type_map.items():
        for field_name, field in getattr(type_def, "fields", {}).items():
            found.append((type_name, field_name, getattr(field, "default_value", None)))
    return found


class TestUnsetDefaultsInSchema:
    def test_no_input_field_defaults_to_an_unset_marker(self) -> None:
        leaked = [
            (type_name, field_name)
            for type_name, field_name, default in _input_defaults()
            if isinstance(default, (Sentinel, Unset))
        ]
        assert leaked == []

    def test_sdl_prints_no_unset_marker(self) -> None:
        sdl = schema.as_str()
        assert '= "MISSING"' not in sdl
        assert "= SENTINEL" not in sdl
