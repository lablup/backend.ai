"""Query conditions for the login_client_type domain."""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.repositories.base import QueryCondition


class LoginClientTypeConditions:
    """QueryCondition factories for login client type filtering."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginClientTypeRow.name.ilike(f"%{spec.value}%")
            else:
                condition = LoginClientTypeRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(LoginClientTypeRow.name) == spec.value.lower()
            else:
                condition = LoginClientTypeRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginClientTypeRow.name.ilike(f"{spec.value}%")
            else:
                condition = LoginClientTypeRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginClientTypeRow.name.ilike(f"%{spec.value}")
            else:
                condition = LoginClientTypeRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(LoginClientTypeRow.name))

    @staticmethod
    def by_description_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            col = sa.func.coalesce(LoginClientTypeRow.description, "")
            if spec.case_insensitive:
                condition = col.ilike(f"%{spec.value}%")
            else:
                condition = col.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            col = sa.func.coalesce(LoginClientTypeRow.description, "")
            if spec.case_insensitive:
                condition = sa.func.lower(col) == spec.value.lower()
            else:
                condition = col == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            col = sa.func.coalesce(LoginClientTypeRow.description, "")
            if spec.case_insensitive:
                condition = col.ilike(f"{spec.value}%")
            else:
                condition = col.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            col = sa.func.coalesce(LoginClientTypeRow.description, "")
            if spec.case_insensitive:
                condition = col.ilike(f"%{spec.value}")
            else:
                condition = col.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_description_in = staticmethod(make_string_in_factory(LoginClientTypeRow.description))

    # --- created_at datetime filters ---

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return LoginClientTypeRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return LoginClientTypeRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return LoginClientTypeRow.created_at == dt

        return inner

    # --- modified_at datetime filters ---

    @staticmethod
    def by_modified_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return LoginClientTypeRow.modified_at < dt

        return inner

    @staticmethod
    def by_modified_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return LoginClientTypeRow.modified_at > dt

        return inner

    @staticmethod
    def by_modified_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return LoginClientTypeRow.modified_at == dt

        return inner
