from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from graphql import GraphQLError

from ai.backend.manager.api.gql_legacy.schema import GQLExceptionMiddleware
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.errors.image import AliasImageActionDBError, ImageNotFound
from ai.backend.manager.errors.repository import UniqueConstraintViolationError


def _db_error() -> sa.exc.IntegrityError:
    return sa.exc.IntegrityError(
        "SELECT users.password FROM users", {}, Exception("relation does not exist")
    )


class TestGQLExceptionMiddleware:
    def test_a_client_error_keeps_its_message(self) -> None:
        error = ImageNotFound("python:3.13")

        def resolver(root: Any, info: Any) -> Any:
            raise error

        with pytest.raises(GraphQLError) as caught:
            GQLExceptionMiddleware().resolve(resolver, None, MagicMock())
        assert caught.value.message == str(error)

    def test_a_server_error_answers_with_its_title(self) -> None:
        def resolver(root: Any, info: Any) -> Any:
            raise AliasImageActionDBError(str(_db_error()))

        with pytest.raises(GraphQLError) as caught:
            GQLExceptionMiddleware().resolve(resolver, None, MagicMock())
        assert caught.value.message == AliasImageActionDBError.error_title

    def test_an_integrity_error_answers_with_its_title_without_the_pg_diagnostic(self) -> None:
        def resolver(root: Any, info: Any) -> Any:
            raise UniqueConstraintViolationError(
                extra_msg='duplicate key value violates unique constraint "uq_users_username"',
                constraint_name="uq_users_username",
            )

        with pytest.raises(GraphQLError) as caught:
            GQLExceptionMiddleware().resolve(resolver, None, MagicMock())
        assert caught.value.message == UniqueConstraintViolationError.error_title

    def test_a_sync_resolver_error_is_masked(self) -> None:
        def resolver(root: Any, info: Any) -> Any:
            raise _db_error()

        with pytest.raises(GraphQLError) as caught:
            GQLExceptionMiddleware().resolve(resolver, None, MagicMock())
        assert caught.value.message == InternalServerError.error_title

    async def test_an_async_resolver_error_is_masked(self) -> None:
        async def resolver(root: Any, info: Any) -> Any:
            raise _db_error()

        with pytest.raises(GraphQLError) as caught:
            await GQLExceptionMiddleware().resolve(resolver, None, MagicMock())
        assert caught.value.message == InternalServerError.error_title

    def test_a_graphql_error_passes_through(self) -> None:
        error = GraphQLError("Cannot query 'x'.")

        def resolver(root: Any, info: Any) -> Any:
            raise error

        with pytest.raises(GraphQLError) as caught:
            GQLExceptionMiddleware().resolve(resolver, None, MagicMock())
        assert caught.value is error
