from collections.abc import Iterable

from .types import ActionOperationType, ActionSpec, OperationStatus

__all__ = ("AuditLogPolicy",)


class AuditLogPolicy:
    """Decides whether an action run is written to the audit log.

    | Case                                | Recorded |
    |-------------------------------------|----------|
    | anything that failed or was denied  | always   |
    | successful mutation                 | always   |
    | successful read, operation opted in | yes      |
    | successful read, otherwise          | no       |

    Mutating operations are deliberately not configurable: an audit trail whose
    minimum guarantee can be switched off is not one. Reads are opt-in because they
    are what generates volume, and opting one in covers every entity type.
    """

    _record_read_operations: frozenset[ActionOperationType]

    def __init__(self, record_read_operations: Iterable[ActionOperationType]) -> None:
        self._record_read_operations = frozenset(record_read_operations)

    def should_record(self, spec: ActionSpec, status: OperationStatus) -> bool:
        if status is not OperationStatus.SUCCESS:
            return True
        if spec.operation_type not in ActionOperationType.read_operations():
            return True
        return spec.operation_type in self._record_read_operations
