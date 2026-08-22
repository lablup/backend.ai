from abc import ABC

__all__ = ("OpsBackendAction",)


class OpsBackendAction(ABC):
    """Executed directly against repository ops; no service method needed.

    Mixed in alongside the shape axis (``BaseScopeAction``, ``BaseSingleEntityAction``,
    ...), which stays responsible for RBAC and audit. This axis only says how the action
    is backed: it carries the repository spec instead of a hand-written service method.
    Promote the action to a real service method as soon as it grows a branch.

    Not a new contract: actions across the codebase already hold a ``Creator`` /
    ``Updater`` / ``Purger`` / ``Upserter`` as a field. This names that contract so a
    generic service can execute it.

    There is deliberately no ``delete`` variant. A soft delete is a status transition,
    so it carries a ``DataUpdater`` like any other write and runs through the update
    service; ``repositories/base/`` has no deleter spec because there is no delete
    operation to generalize.
    """
