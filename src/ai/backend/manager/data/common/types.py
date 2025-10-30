from dataclasses import dataclass
from typing import Optional


@dataclass
class StringFilterData:
    """Data class that corresponds 1:1 with StringFilter for API requests."""

    contains: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    equals: Optional[str] = None
    not_equals: Optional[str] = None
    i_contains: Optional[str] = None
    i_starts_with: Optional[str] = None
    i_ends_with: Optional[str] = None
    i_equals: Optional[str] = None
    i_not_equals: Optional[str] = None

    def apply_to_column(self, column):
        """Apply this string filter to a SQLAlchemy column and return the condition.

        Args:
            column: SQLAlchemy column to apply the filter to

        Returns:
            SQLAlchemy condition expression or None if no filter is set
        """
        if self.equals is not None:
            return column == self.equals
        elif self.i_equals is not None:
            return column.ilike(self.i_equals)
        elif self.not_equals is not None:
            return column != self.not_equals
        elif self.i_not_equals is not None:
            return ~column.ilike(self.i_not_equals)
        elif self.starts_with is not None:
            return column.like(f"{self.starts_with}%")
        elif self.i_starts_with is not None:
            return column.ilike(f"{self.i_starts_with}%")
        elif self.ends_with is not None:
            return column.like(f"%{self.ends_with}")
        elif self.i_ends_with is not None:
            return column.ilike(f"%{self.i_ends_with}")
        elif self.contains is not None:
            return column.like(f"%{self.contains}%")
        elif self.i_contains is not None:
            return column.ilike(f"%{self.i_contains}%")

        return None


@dataclass
class IntFilterData:
    """Data class that corresponds 1:1 with IntFilter for API requests."""

    equals: Optional[int] = None
    not_equals: Optional[int] = None
    greater_than: Optional[int] = None
    greater_than_or_equal: Optional[int] = None
    less_than: Optional[int] = None
    less_than_or_equal: Optional[int] = None

    def apply_to_column(self, column):
        """Apply this int filter to a SQLAlchemy column and return the condition.

        Args:
            column: SQLAlchemy column to apply the filter to

        Returns:
            SQLAlchemy condition expression or None if no filter is set
        """
        if self.equals is not None:
            return column == self.equals
        elif self.not_equals is not None:
            return column != self.not_equals
        elif self.greater_than is not None:
            return column > self.greater_than
        elif self.greater_than_or_equal is not None:
            return column >= self.greater_than_or_equal
        elif self.less_than is not None:
            return column < self.less_than
        elif self.less_than_or_equal is not None:
            return column <= self.less_than_or_equal

        return None
