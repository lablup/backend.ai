"""Frozen copies of the RBAC models and enums the data migrations were written
against.

Deprecated: nothing outside `models/alembic/versions/` may read this package. It does
not track the live models, and the `grant:*` operations it still lists are retired --
sharing an entity is `entity_share`, not a permission bit.
"""
