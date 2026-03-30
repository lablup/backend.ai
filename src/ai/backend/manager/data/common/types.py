from dataclasses import dataclass

from sqlalchemy.sql.elements import ColumnElement


@dataclass(frozen=True)
class SearchResult[T]:
    items: list[T]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class StringFilterData:
    """Data class that corresponds 1:1 with StringFilter for API requests."""

    contains: str | None = None
    starts_with: str | None = None
    ends_with: str | None = None
    equals: str | None = None
    not_equals: str | None = None
    i_contains: str | None = None
    i_starts_with: str | None = None
    i_ends_with: str | None = None
    i_equals: str | None = None
    i_not_equals: str | None = None

    def apply_to_column(self, column: ColumnElement[str]) -> ColumnElement[bool] | None:
        """Apply this string filter to a SQLAlchemy column and return the condition.

        Args:
            column: SQLAlchemy column to apply the filter to

        Returns:
            SQLAlchemy condition expression or None if no filter is set
        """
        if self.equals is not None:
            return column == self.equals
        if self.i_equals is not None:
            return column.ilike(self.i_equals)
        if self.not_equals is not None:
            return column != self.not_equals
        if self.i_not_equals is not None:
            return ~column.ilike(self.i_not_equals)
        if self.starts_with is not None:
            return column.like(f"{self.starts_with}%")
        if self.i_starts_with is not None:
            return column.ilike(f"{self.i_starts_with}%")
        if self.ends_with is not None:
            return column.like(f"%{self.ends_with}")
        if self.i_ends_with is not None:
            return column.ilike(f"%{self.i_ends_with}")
        if self.contains is not None:
            return column.like(f"%{self.contains}%")
        if self.i_contains is not None:
            return column.ilike(f"%{self.i_contains}%")

        return None


@dataclass
class IntFilterData:
    """Data class that corresponds 1:1 with IntFilter for API requests."""

    equals: int | None = None
    not_equals: int | None = None
    greater_than: int | None = None
    greater_than_or_equal: int | None = None
    less_than: int | None = None
    less_than_or_equal: int | None = None

    def apply_to_column(self, column: ColumnElement[int]) -> ColumnElement[bool] | None:
        """Apply this int filter to a SQLAlchemy column and return the condition.

        Args:
            column: SQLAlchemy column to apply the filter to

        Returns:
            SQLAlchemy condition expression or None if no filter is set
        """
        if self.equals is not None:
            return column == self.equals
        if self.not_equals is not None:
            return column != self.not_equals
        if self.greater_than is not None:
            return column > self.greater_than
        if self.greater_than_or_equal is not None:
            return column >= self.greater_than_or_equal
        if self.less_than is not None:
            return column < self.less_than
        if self.less_than_or_equal is not None:
            return column <= self.less_than_or_equal

        return None
