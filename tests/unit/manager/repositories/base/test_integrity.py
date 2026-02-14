"""Unit tests for integrity error parser and matcher."""

from __future__ import annotations

import asyncpg.exceptions
import pytest
import sqlalchemy as sa

from ai.backend.manager.errors.repository import (
    CheckConstraintViolationError,
    ExclusionViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    RepositoryIntegrityError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.repositories.base.integrity import (
    _match_integrity_error,
    parse_integrity_error,
)
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


def _make_asyncpg_error(
    *,
    sqlstate: str,
    message: str = "some error",
    constraint_name: str | None = None,
    table_name: str | None = None,
    column_name: str | None = None,
    detail: str | None = None,
) -> asyncpg.exceptions.PostgresError:
    """Create an asyncpg PostgresError using its ``new()`` factory."""
    fields: dict[str, str] = {"C": sqlstate, "M": message}
    if constraint_name is not None:
        fields["n"] = constraint_name
    if table_name is not None:
        fields["t"] = table_name
    if column_name is not None:
        fields["c"] = column_name
    if detail is not None:
        fields["D"] = detail
    return asyncpg.exceptions.PostgresError.new(fields)


def _make_integrity_error(
    *,
    sqlstate: str | None = None,
    message: str = "some error",
    constraint_name: str | None = None,
    table_name: str | None = None,
    column_name: str | None = None,
    detail: str | None = None,
) -> sa.exc.IntegrityError:
    """Create a mock SQLAlchemy IntegrityError with asyncpg-like orig."""
    if sqlstate is not None:
        orig: Exception = _make_asyncpg_error(
            sqlstate=sqlstate,
            message=message,
            constraint_name=constraint_name,
            table_name=table_name,
            column_name=column_name,
            detail=detail,
        )
    else:
        orig = Exception(message)
    return sa.exc.IntegrityError(
        statement="INSERT INTO ...",
        params={},
        orig=orig,
    )


class TestParseIntegrityErrorBySQLSTATE:
    """Test SQLSTATE-based classification."""

    @pytest.mark.parametrize(
        ("pgcode", "expected_cls"),
        [
            ("23505", UniqueConstraintViolationError),
            ("23503", ForeignKeyViolationError),
            ("23514", CheckConstraintViolationError),
            ("23502", NotNullViolationError),
            ("23P01", ExclusionViolationError),
        ],
    )
    def test_classifies_by_sqlstate(
        self,
        pgcode: str,
        expected_cls: type[RepositoryIntegrityError],
    ) -> None:
        e = _make_integrity_error(sqlstate=pgcode)
        result = parse_integrity_error(e)
        assert isinstance(result, expected_cls)
        assert result.pgcode == pgcode

    def test_extracts_diag_attributes(self) -> None:
        e = _make_integrity_error(
            sqlstate="23505",
            constraint_name="uq_users_email",
            table_name="users",
            column_name="email",
            detail="Key (email)=(test@example.com) already exists.",
        )
        result = parse_integrity_error(e)
        assert isinstance(result, UniqueConstraintViolationError)
        assert result.constraint_name == "uq_users_email"
        assert result.table_name == "users"
        assert result.column_name == "email"
        assert result.detail == "Key (email)=(test@example.com) already exists."

    def test_unknown_sqlstate_falls_back_to_generic(self) -> None:
        e = _make_integrity_error(sqlstate="23999")
        result = parse_integrity_error(e)
        assert type(result) is RepositoryIntegrityError
        assert result.pgcode == "23999"


class TestParseIntegrityErrorByMessage:
    """Test message-based fallback classification."""

    @pytest.mark.parametrize(
        ("message", "expected_cls"),
        [
            (
                'duplicate key value violates unique constraint "uq_name"',
                UniqueConstraintViolationError,
            ),
            (
                "unique violation on column email",
                UniqueConstraintViolationError,
            ),
            (
                'insert or update on table "orders" violates foreign key constraint',
                ForeignKeyViolationError,
            ),
            (
                'not-null constraint violated for column "name"',
                NotNullViolationError,
            ),
            (
                'null value in column "email" of relation "users" violates not-null',
                NotNullViolationError,
            ),
            (
                'new row for relation "events" violates check constraint "positive_count"',
                CheckConstraintViolationError,
            ),
            (
                "conflicting key value violates exclusion constraint",
                ExclusionViolationError,
            ),
        ],
    )
    def test_classifies_by_message(
        self,
        message: str,
        expected_cls: type[RepositoryIntegrityError],
    ) -> None:
        e = _make_integrity_error(message=message)
        result = parse_integrity_error(e)
        assert isinstance(result, expected_cls)

    def test_unrecognized_message_falls_back_to_generic(self) -> None:
        e = _make_integrity_error(message="something unexpected happened")
        result = parse_integrity_error(e)
        assert type(result) is RepositoryIntegrityError


class TestParseIntegrityErrorWithoutDiag:
    """Test graceful handling when asyncpg diagnostic attributes are unavailable."""

    def test_no_diag_attributes_are_none(self) -> None:
        e = _make_integrity_error(sqlstate="23505")
        result = parse_integrity_error(e)
        assert isinstance(result, UniqueConstraintViolationError)
        assert result.constraint_name is None
        assert result.table_name is None
        assert result.column_name is None
        assert result.detail is None

    def test_no_pgcode_uses_message_fallback(self) -> None:
        e = _make_integrity_error(
            message='duplicate key value violates unique constraint "uq_name"',
        )
        result = parse_integrity_error(e)
        assert isinstance(result, UniqueConstraintViolationError)
        assert result.pgcode is None


class TestMatchIntegrityError:
    """Test _match_integrity_error matching logic."""

    def _make_domain_error(self, msg: str = "domain error") -> RepositoryIntegrityError:
        """Create a simple domain error for use in checks."""
        return UniqueConstraintViolationError(extra_msg=msg)

    def test_matches_by_violation_type(self) -> None:
        parsed = UniqueConstraintViolationError(
            extra_msg="dup",
            constraint_name="uq_name",
        )
        domain_error = self._make_domain_error("name already exists")
        checks = [
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=domain_error,
            ),
        ]
        with pytest.raises(UniqueConstraintViolationError, match="name already exists") as exc_info:
            _match_integrity_error(parsed, checks)
        assert exc_info.value is domain_error
        assert exc_info.value.__cause__ is parsed

    def test_matches_by_violation_type_and_constraint_name(self) -> None:
        parsed = UniqueConstraintViolationError(
            extra_msg="dup",
            constraint_name="uq_users_email",
        )
        email_error = self._make_domain_error("email taken")
        name_error = self._make_domain_error("name taken")
        checks = [
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=name_error,
                constraint_name="uq_users_name",
            ),
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=email_error,
                constraint_name="uq_users_email",
            ),
        ]
        with pytest.raises(UniqueConstraintViolationError) as exc_info:
            _match_integrity_error(parsed, checks)
        assert exc_info.value is email_error

    def test_no_match_raises_parsed_error(self) -> None:
        parsed = ForeignKeyViolationError(
            extra_msg="fk violation",
            constraint_name="fk_orders_user",
        )
        checks = [
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=self._make_domain_error(),
            ),
        ]
        with pytest.raises(ForeignKeyViolationError) as exc_info:
            _match_integrity_error(parsed, checks)
        assert exc_info.value is parsed

    def test_empty_checks_raises_parsed_error(self) -> None:
        parsed = UniqueConstraintViolationError(extra_msg="dup")
        with pytest.raises(UniqueConstraintViolationError) as exc_info:
            _match_integrity_error(parsed, [])
        assert exc_info.value is parsed

    def test_constraint_name_mismatch_skips_check(self) -> None:
        parsed = UniqueConstraintViolationError(
            extra_msg="dup",
            constraint_name="uq_other",
        )
        checks = [
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=self._make_domain_error("specific"),
                constraint_name="uq_users_email",
            ),
        ]
        with pytest.raises(UniqueConstraintViolationError) as exc_info:
            _match_integrity_error(parsed, checks)
        # Falls through to parsed error since constraint name doesn't match
        assert exc_info.value is parsed

    def test_none_constraint_name_in_check_matches_any(self) -> None:
        parsed = UniqueConstraintViolationError(
            extra_msg="dup",
            constraint_name="uq_whatever",
        )
        domain_error = self._make_domain_error("catch all unique")
        checks = [
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=domain_error,
                constraint_name=None,  # matches any
            ),
        ]
        with pytest.raises(UniqueConstraintViolationError) as exc_info:
            _match_integrity_error(parsed, checks)
        assert exc_info.value is domain_error
