from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from graphql import GraphQLError
from pydantic import BaseModel, ValidationError

from ai.backend.common.exception import BackendAISchemaValidationFailed, ErrorCode
from ai.backend.manager.api.gql.extensions.exception_handler import GQLExceptionHandlerExtension
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.errors.image import AliasImageActionDBError, ImageNotFound
from ai.backend.manager.errors.repository import UniqueConstraintViolationError

_PG_DIAGNOSTIC = (
    'duplicate key value violates unique constraint "uq_image_aliases_alias"\n'
    "DETAIL:  Key (alias)=(python) already exists."
)


class _Event(BaseModel):
    count: int


def _validation_error() -> ValidationError:
    try:
        _Event.model_validate({"count": "not-a-number"})
    except ValidationError as e:
        return e
    raise AssertionError("expected a ValidationError")


def _db_error() -> sa.exc.IntegrityError:
    return sa.exc.IntegrityError(
        "INSERT INTO image_aliases (alias, image) VALUES (%(alias)s, %(image)s)",
        {"alias": "python", "image": "x"},
        Exception(_PG_DIAGNOSTIC),
    )


def _raised_through(extension: GQLExceptionHandlerExtension, exc: Exception) -> GraphQLError:
    def resolver(root: Any, info: Any) -> Any:
        raise exc

    with pytest.raises(GraphQLError) as caught:
        extension.resolve(resolver, None, MagicMock())
    return caught.value


class TestGQLExceptionHandlerResponses:
    @pytest.fixture
    def extension(self) -> GQLExceptionHandlerExtension:
        return GQLExceptionHandlerExtension()

    def test_a_client_error_keeps_its_message_and_code(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        e = ImageNotFound("python:3.13")
        converted = _raised_through(extension, e)
        assert converted.message == str(e)
        assert converted.extensions == {"code": str(e.error_code())}

    def test_an_integrity_error_answers_with_its_title_without_the_pg_diagnostic(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        e = UniqueConstraintViolationError(
            extra_msg=_PG_DIAGNOSTIC, constraint_name="uq_image_aliases_alias"
        )
        converted = _raised_through(extension, e)
        assert converted.message == UniqueConstraintViolationError.error_title
        assert converted.extensions == {"code": str(e.error_code())}

    def test_a_server_error_answers_with_its_title_without_the_db_text(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        e = AliasImageActionDBError(str(_db_error()))
        converted = _raised_through(extension, e)
        assert converted.message == AliasImageActionDBError.error_title
        assert converted.extensions == {"code": str(e.error_code())}

    def test_an_unexpected_error_answers_with_a_fixed_message_and_the_default_code(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        converted = _raised_through(extension, _db_error())
        assert converted.message == InternalServerError.error_title
        assert converted.extensions == {"code": str(ErrorCode.default())}

    def test_a_validation_error_answers_as_a_400_with_its_field_errors(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        converted = _raised_through(extension, _validation_error())
        assert converted.extensions is not None
        assert converted.extensions["code"] == str(
            BackendAISchemaValidationFailed(extra_msg="").error_code()
        )
        assert [err["loc"] for err in converted.extensions["errors"]] == [("count",)]


class TestGQLExceptionHandlerExtension:
    @pytest.fixture
    def extension(self) -> GQLExceptionHandlerExtension:
        return GQLExceptionHandlerExtension()

    def test_a_sync_resolver_error_is_masked(self, extension: GQLExceptionHandlerExtension) -> None:
        def resolver(root: Any, info: Any) -> Any:
            raise _db_error()

        with pytest.raises(GraphQLError) as caught:
            extension.resolve(resolver, None, MagicMock())
        assert caught.value.message == InternalServerError.error_title

    async def test_an_async_resolver_error_is_masked(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        async def resolver(root: Any, info: Any) -> Any:
            raise _db_error()

        pending = extension.resolve(resolver, None, MagicMock())
        assert asyncio.iscoroutine(pending)
        with pytest.raises(GraphQLError) as caught:
            await pending
        assert caught.value.message == InternalServerError.error_title
