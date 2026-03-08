import enum
from typing import Final, NamedTuple

from graphql_relay.utils import unbase64

DEFAULT_PAGE_SIZE: Final[int] = 10


class ConnectionPaginationOrder(enum.Enum):
    FORWARD = "forward"
    BACKWARD = "backward"


class ConnectionArgs(NamedTuple):
    cursor: str | None
    pagination_order: ConnectionPaginationOrder | None
    requested_page_size: int


def resolve_global_id(global_id: str) -> tuple[str, str]:
    unbased_global_id = unbase64(global_id)
    type_, _, id_ = unbased_global_id.partition(":")
    return type_, id_


def validate_connection_args(
    *,
    after: str | None = None,
    first: int | None = None,
    before: str | None = None,
    last: int | None = None,
) -> ConnectionArgs:
    """
    Validate arguments used for GraphQL relay connection, and determine pagination ordering, cursor and page size.
    It is not allowed to use arguments for forward pagination and arguments for backward pagination at the same time.
    """
    order: ConnectionPaginationOrder | None = None
    cursor: str | None = None
    requested_page_size: int | None = None

    if after is not None:
        order = ConnectionPaginationOrder.FORWARD
        cursor = after
    if first is not None:
        if first < 0:
            raise ValueError("Argument 'first' must be a non-negative integer.")
        order = ConnectionPaginationOrder.FORWARD
        requested_page_size = first

    if before is not None:
        if order is ConnectionPaginationOrder.FORWARD:
            raise ValueError(
                "Can only paginate with single direction, forwards or backwards. Please set only"
                " one of (after, first) or (before, last)."
            )
        order = ConnectionPaginationOrder.BACKWARD
        cursor = before
    if last is not None:
        if last < 0:
            raise ValueError("Argument 'last' must be a non-negative integer.")
        if order is ConnectionPaginationOrder.FORWARD:
            raise ValueError(
                "Can only paginate with single direction, forwards or backwards. Please set only"
                " one of (after, first) or (before, last)."
            )
        order = ConnectionPaginationOrder.BACKWARD
        requested_page_size = last

    if requested_page_size is None:
        requested_page_size = DEFAULT_PAGE_SIZE

    return ConnectionArgs(cursor, order, requested_page_size)
