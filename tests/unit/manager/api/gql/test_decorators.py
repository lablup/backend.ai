"""Tests for gql_pydantic_input's @oneOf guard.

A `@oneOf` input field must not carry a schema default: GraphQL forbids it, and a
default puts every key into the coerced input so the server rejects the request.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from graphql import GraphQLInputObjectType, Undefined
from pydantic import BaseModel
from strawberry import UNSET
from strawberry.types.base import get_object_definition

from ai.backend.common.meta import BackendAIGQLMeta
from ai.backend.manager.api.gql.decorators import (
    gql_added_field,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin
from ai.backend.manager.api.gql.schema import schema

META = BackendAIGQLMeta(added_version="26.9.0", description="Recipient of an offer.")


class RecipientDTO(BaseModel):
    project_id: UUID | None = None
    user_id: UUID | None = None


class TestOneOfInputsInSchema:
    def test_no_one_of_input_field_carries_a_default(self) -> None:
        one_of_types = [
            (type_name, type_def)
            for type_name, type_def in schema._schema.type_map.items()
            if isinstance(type_def, GraphQLInputObjectType)
            # Strawberry marks @oneOf on its own definition, not on the core type.
            and getattr(type_def.extensions.get("strawberry-definition"), "is_one_of", False)
        ]
        assert one_of_types, "the schema holds no @oneOf input to check"
        defaulted = [
            f"{type_name}.{field_name}"
            for type_name, type_def in one_of_types
            for field_name, field in type_def.fields.items()
            if field.default_value is not Undefined
        ]
        assert defaulted == []


class TestOneOfInputDeclaration:
    def test_a_none_default_is_rejected(self) -> None:
        with pytest.raises(ValueError):

            @gql_pydantic_input(META, name="NoneDefaultRecipientInput", one_of=True)
            class _NoneDefault(PydanticInputMixin[RecipientDTO]):
                project_id: UUID | None = gql_field(
                    default=None, description="Project the offer goes to."
                )
                user_id: UUID | None = gql_field(
                    default=UNSET, description="Person the offer goes to."
                )

    def test_a_default_factory_is_rejected(self) -> None:
        # Strawberry evaluates the factory into the schema default, so it leaks too.
        with pytest.raises(ValueError):

            @gql_pydantic_input(META, name="FactoryRecipientInput", one_of=True)
            class _FactoryDefault(PydanticInputMixin[RecipientDTO]):
                project_id: list[UUID] = gql_added_field(META, default_factory=list)
                user_id: UUID | None = gql_field(
                    default=UNSET, description="Person the offer goes to."
                )

    def test_unset_defaults_are_accepted(self) -> None:
        @gql_pydantic_input(META, name="UnsetRecipientInput", one_of=True)
        class _Unset(PydanticInputMixin[RecipientDTO]):
            project_id: UUID | None = gql_field(
                default=UNSET, description="Project the offer goes to."
            )
            user_id: UUID | None = gql_field(default=UNSET, description="Person the offer goes to.")

        defaults = [
            field.default_value for field in get_object_definition(_Unset, strict=True).fields
        ]
        assert defaults == [UNSET, UNSET]


class TestPlainInputDeclaration:
    def test_a_none_default_is_accepted_without_one_of(self) -> None:
        @gql_pydantic_input(META, name="PlainRecipientInput")
        class _Plain(PydanticInputMixin[RecipientDTO]):
            project_id: UUID | None = gql_field(
                default=None, description="Project the offer goes to."
            )

        defaults = [
            field.default_value for field in get_object_definition(_Plain, strict=True).fields
        ]
        assert defaults == [None]
