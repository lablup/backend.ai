from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from graphql import OperationDefinitionNode, parse, validate
from graphql.execution.values import get_variable_values
from strawberry.types.arguments import convert_argument

from ai.backend.common.dto.manager.v2.entity_share.request import EntityShareRecipientInput
from ai.backend.manager.api.gql.entity_share.types import CreateEntityShareInputGQL
from ai.backend.manager.api.gql.schema import schema

_MUTATION = """
mutation ($input: CreateEntityShareInput!) {
  createEntityShare(input: $input) { share { id } }
}
"""
_TARGET_ID = "00000000-0000-0000-0000-0000000000aa"


def _coerce_recipient(recipient: dict[str, Any]) -> EntityShareRecipientInput | list[str]:
    operation = parse(_MUTATION).definitions[0]
    assert isinstance(operation, OperationDefinitionNode)
    coerced = get_variable_values(
        schema._schema,
        operation.variable_definitions,
        {
            "input": {
                "targetEntityType": "vfolder",
                "targetEntityId": _TARGET_ID,
                "recipient": recipient,
            }
        },
    )
    if isinstance(coerced, list):
        return [error.message for error in coerced]
    input_ = convert_argument(
        coerced["input"],
        CreateEntityShareInputGQL,
        schema.schema_converter.scalar_registry,
        schema.config,
    )
    assert isinstance(input_, CreateEntityShareInputGQL)
    return input_.to_pydantic().recipient


class TestEntityShareRecipientInput:
    @pytest.mark.parametrize(
        ("recipient", "expected"),
        [
            (
                {"projectId": str(UUID(int=1))},
                EntityShareRecipientInput(project_id=UUID(int=1)),
            ),
            (
                {"userId": str(UUID(int=2))},
                EntityShareRecipientInput(user_id=UUID(int=2)),
            ),
            (
                {"email": "someone@example.com"},
                EntityShareRecipientInput(email="someone@example.com"),
            ),
        ],
    )
    def test_one_key_variable_passes_one_of_and_converts_to_dto(
        self, recipient: dict[str, Any], expected: EntityShareRecipientInput
    ) -> None:
        assert _coerce_recipient(recipient) == expected

    def test_one_key_inline_literal_passes_one_of(self) -> None:
        document = parse(f"""
            mutation {{
              createEntityShare(input: {{
                targetEntityType: "vfolder"
                targetEntityId: "{_TARGET_ID}"
                recipient: {{userId: "{UUID(int=2)}"}}
              }}) {{ share {{ id }} }}
            }}
        """)

        assert validate(schema._schema, document) == []

    def test_two_keys_are_rejected(self) -> None:
        errors = _coerce_recipient({"userId": str(UUID(int=2)), "email": "someone@example.com"})

        assert isinstance(errors, list)
        assert any("must specify exactly one key" in message for message in errors)

    def test_sdl_fields_have_no_default(self) -> None:
        sdl = schema.as_str()
        start = sdl.index("input EntityShareRecipientInput")
        block = sdl[start : sdl.index("}", start)]

        assert "= null" not in block
