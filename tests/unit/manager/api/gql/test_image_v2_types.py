from __future__ import annotations

from ai.backend.manager.api.gql.schema import schema


def test_image_v2_schema_exposes_installed_field() -> None:
    sdl = schema.as_str()
    image_type = sdl.split("type ImageV2 implements Node {", maxsplit=1)[1].split(
        "\n}", maxsplit=1
    )[0]

    assert "installed: Boolean!" in image_type
