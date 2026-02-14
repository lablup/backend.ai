"""Unit tests for RepositoryIntegrityError hierarchy."""

from __future__ import annotations

import pytest
from aiohttp import web

from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    ExclusionViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    RepositoryError,
    RepositoryIntegrityError,
    UniqueConstraintViolationError,
)


class TestRepositoryIntegrityErrorHierarchy:
    """Test that the error hierarchy is correct."""

    def test_inherits_from_repository_error(self) -> None:
        err = RepositoryIntegrityError()
        assert isinstance(err, RepositoryError)

    def test_inherits_from_http_conflict(self) -> None:
        err = RepositoryIntegrityError()
        assert isinstance(err, web.HTTPConflict)

    @pytest.mark.parametrize(
        "cls",
        [
            UniqueConstraintViolationError,
            ForeignKeyViolationError,
            CheckConstraintViolationError,
            NotNullViolationError,
            ExclusionViolationError,
        ],
    )
    def test_subclasses_inherit_from_base(self, cls: type[RepositoryIntegrityError]) -> None:
        err = cls()
        assert isinstance(err, RepositoryIntegrityError)
        assert isinstance(err, RepositoryError)


class TestRepositoryIntegrityErrorAttributes:
    """Test structured attribute access."""

    def test_default_attributes_are_none(self) -> None:
        err = RepositoryIntegrityError()
        assert err.constraint_name is None
        assert err.table_name is None
        assert err.column_name is None
        assert err.detail is None
        assert err.pgcode is None

    def test_attributes_set_via_constructor(self) -> None:
        err = UniqueConstraintViolationError(
            extra_msg="duplicate key",
            constraint_name="uq_users_email",
            table_name="users",
            column_name="email",
            detail="Key (email)=(test@example.com) already exists.",
            pgcode="23505",
        )
        assert err.constraint_name == "uq_users_email"
        assert err.table_name == "users"
        assert err.column_name == "email"
        assert err.detail == "Key (email)=(test@example.com) already exists."
        assert err.pgcode == "23505"

    def test_extra_msg_propagation(self) -> None:
        err = RepositoryIntegrityError(extra_msg="some detail")
        assert err.extra_msg == "some detail"


class TestErrorCodes:
    """Test error_code() returns correct ErrorDetail."""

    def test_unique_constraint_error_detail(self) -> None:
        err = UniqueConstraintViolationError()
        assert err.error_code().error_detail == ErrorDetail.ALREADY_EXISTS

    def test_foreign_key_error_detail(self) -> None:
        err = ForeignKeyViolationError()
        assert err.error_code().error_detail == ErrorDetail.NOT_FOUND

    def test_check_constraint_error_detail(self) -> None:
        err = CheckConstraintViolationError()
        assert err.error_code().error_detail == ErrorDetail.CONFLICT

    def test_not_null_error_detail(self) -> None:
        err = NotNullViolationError()
        assert err.error_code().error_detail == ErrorDetail.BAD_REQUEST

    def test_exclusion_error_detail(self) -> None:
        err = ExclusionViolationError()
        assert err.error_code().error_detail == ErrorDetail.CONFLICT

    def test_base_integrity_error_detail(self) -> None:
        err = RepositoryIntegrityError()
        assert err.error_code().error_detail == ErrorDetail.CONFLICT


class TestHTTPStatusCodes:
    """Test HTTP status code mapping."""

    def test_integrity_error_is_409(self) -> None:
        err = RepositoryIntegrityError()
        assert err.status_code == 409

    def test_unique_constraint_is_409(self) -> None:
        err = UniqueConstraintViolationError()
        assert err.status_code == 409

    def test_foreign_key_is_409(self) -> None:
        err = ForeignKeyViolationError()
        assert err.status_code == 409

    def test_check_constraint_is_409(self) -> None:
        err = CheckConstraintViolationError()
        assert err.status_code == 409

    def test_not_null_is_400(self) -> None:
        err = NotNullViolationError()
        assert err.status_code == 400

    def test_exclusion_is_409(self) -> None:
        err = ExclusionViolationError()
        assert err.status_code == 409
