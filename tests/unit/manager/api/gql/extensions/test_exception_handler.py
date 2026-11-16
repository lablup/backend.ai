from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from graphql import GraphQLError
from pydantic import BaseModel, ValidationError
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types.execution import ExecutionResult
from strawberry.types.graphql import OperationType

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


class TestOnStreamResult:
    @pytest.fixture
    def extension(self) -> GQLExceptionHandlerExtension:
        return GQLExceptionHandlerExtension()

    def _stream(self, extension: GQLExceptionHandlerExtension, result: ExecutionResult) -> None:
        hook = extension.on_stream_result(result)
        next(hook)

    def test_an_error_raised_while_streaming_is_masked(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        # Strawberry wraps an exception from a subscription stream like this.
        exc = _db_error()
        result = ExecutionResult(data=None, errors=[GraphQLError(str(exc), original_error=exc)])
        self._stream(extension, result)
        assert result.errors is not None
        assert [e.message for e in result.errors] == [InternalServerError.error_title]
        assert result.errors[0].extensions == {"code": str(ErrorCode.default())}

    def test_a_streamed_error_is_logged_with_its_traceback(
        self, extension: GQLExceptionHandlerExtension, caplog: pytest.LogCaptureFixture
    ) -> None:
        try:
            raise _db_error()
        except sa.exc.IntegrityError as raised:
            exc = raised
        result = ExecutionResult(data=None, errors=[GraphQLError(str(exc), original_error=exc)])
        with caplog.at_level(logging.ERROR):
            self._stream(extension, result)
        logged = [record for record in caplog.records if record.exc_info is not None]
        assert [record.exc_info[1] for record in logged if record.exc_info] == [exc]
        assert logged[0].exc_info is not None
        assert logged[0].exc_info[2] is not None

    def test_a_validation_error_raised_while_streaming_stays_a_client_error(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        exc = _validation_error()
        result = ExecutionResult(data=None, errors=[GraphQLError(str(exc), original_error=exc)])
        self._stream(extension, result)
        assert result.errors is not None
        assert result.errors[0].message != InternalServerError.error_title
        assert result.errors[0].extensions is not None
        assert result.errors[0].extensions["code"] == str(
            BackendAISchemaValidationFailed(extra_msg="").error_code()
        )

    def test_a_pre_execution_error_keeps_its_message(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        # Strawberry answers a subscription sent where none is allowed like this.
        error = GraphQLError(
            "subscriptions are not allowed",
            original_error=InvalidOperationTypeError(OperationType.SUBSCRIPTION),
        )
        result = ExecutionResult(data=None, errors=[error])
        self._stream(extension, result)
        assert result.errors == [error]

    def test_an_already_converted_error_is_kept(
        self, extension: GQLExceptionHandlerExtension
    ) -> None:
        error = GraphQLError("Image not found.", extensions={"code": "image_read_not-found"})
        result = ExecutionResult(data=None, errors=[error])
        self._stream(extension, result)
        assert result.errors == [error]
