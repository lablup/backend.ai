from .base import BaseAction


class BaseGlobalAction(BaseAction):
    """Base for super-admin-only actions on the global area.

    A global action targets system-wide config that belongs to no RBAC scope
    (e.g. a super-admin singleton/catalog). Authorization is a SUPERADMIN role
    gate — NOT RBAC scope resolution — so, unlike ``BaseScopeAction`` /
    ``BaseSingleEntityAction``, this base declares neither a scope nor a
    ``target_element``. It carries only ``entity_type`` / ``operation_type``
    from ``BaseAction`` for monitoring; the SUPERADMIN gate is enforced by
    ``GlobalActionProcessor``.
    """
