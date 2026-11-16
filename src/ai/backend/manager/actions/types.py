import enum
from typing import Final

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import ErrorOperation

# Placeholder substituted when an id (request_id, entity_id, ...) is absent while
# materializing action metadata into audit/report records.
BLANK_ID: Final[str] = "(unknown)"


class OperationStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"
    # Rejected by a validator before the action ran. Kept apart from ERROR because a
    # denial is an authorization signal, not the operation failing.
    DENIED = "denied"


class ActionOperationType(enum.StrEnum):
    GET = "get"
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"
    PURGE = "purge"
    RESTORE = "restore"
    LOOKUP = "lookup"

    @classmethod
    def read_operations(cls) -> frozenset["ActionOperationType"]:
        """The operations that only read. Everything else changes state.

        The audit layer draws its "always record" line here: a state change is
        recorded unconditionally, while recording a read is a configurable choice.
        """
        return frozenset({cls.GET, cls.SEARCH, cls.LOOKUP})

    def to_permission_bit(self) -> Permission:
        """The single bit this operation is listed under.

        ``UPSERT`` narrows to ``CREATE``: a listing carries one bit and cannot express
        the ``CREATE | UPDATE`` mask :meth:`to_permission` requires, so it keeps the
        stronger of the two.
        """
        match self:
            case ActionOperationType.GET:
                return Permission.READ
            case ActionOperationType.SEARCH:
                return Permission.READ
            case ActionOperationType.LOOKUP:
                return Permission.READ
            case ActionOperationType.CREATE:
                return Permission.CREATE
            case ActionOperationType.UPDATE:
                return Permission.UPDATE
            case ActionOperationType.UPSERT:
                return Permission.CREATE
            case ActionOperationType.DELETE:
                return Permission.SOFT_DELETE
            case ActionOperationType.PURGE:
                return Permission.HARD_DELETE
            case ActionOperationType.RESTORE:
                return Permission.SOFT_DELETE

    def to_error_operation(self) -> ErrorOperation:
        """The ``ErrorCode`` operation an error raised under this operation reports.

        Every operation but ``LOOKUP`` has its own counterpart. ``LOOKUP`` reads the one
        row a key names, so it reports as a read like ``GET``. ``DELETE`` and ``PURGE``
        report under the names that say which delete they are.
        """
        match self:
            case ActionOperationType.GET | ActionOperationType.LOOKUP:
                return ErrorOperation.READ
            case ActionOperationType.SEARCH:
                return ErrorOperation.SEARCH
            case ActionOperationType.CREATE:
                return ErrorOperation.CREATE
            case ActionOperationType.UPSERT:
                return ErrorOperation.UPSERT
            case ActionOperationType.UPDATE:
                return ErrorOperation.UPDATE
            case ActionOperationType.RESTORE:
                return ErrorOperation.RESTORE
            case ActionOperationType.DELETE:
                return ErrorOperation.SOFT_DELETE
            case ActionOperationType.PURGE:
                return ErrorOperation.HARD_DELETE

    def to_permission(self) -> Permission:
        """The permission an action performing this operation must hold.

        The result is a mask, not necessarily a single bit, and every bit in it is
        required: ``UPSERT`` may insert or overwrite, so demanding only ``CREATE``
        would let it overwrite without ``UPDATE`` and vice versa.

        ``RESTORE`` shares ``SOFT_DELETE``: undoing a soft delete flips one status
        flag back and reaches nothing the deleter could not already reach.
        """
        match self:
            case ActionOperationType.GET | ActionOperationType.SEARCH | ActionOperationType.LOOKUP:
                return Permission.READ
            case ActionOperationType.CREATE:
                return Permission.CREATE
            case ActionOperationType.UPDATE:
                return Permission.UPDATE
            case ActionOperationType.UPSERT:
                return Permission.CREATE | Permission.UPDATE
            case ActionOperationType.DELETE | ActionOperationType.RESTORE:
                return Permission.SOFT_DELETE
            case ActionOperationType.PURGE:
                return Permission.HARD_DELETE
