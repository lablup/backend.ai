"""Backward-compatible shim for the admin module.

GraphQL handler logic has been migrated to:

* ``api.rest.admin.handler`` — AdminHandler class
* ``api.rest.admin`` — route registration

The ``PrivateContext`` and lifecycle hooks (``init``/``shutdown``) have been
removed as part of the DependencyComposer migration.  GQL schema
initialization and introspection warnings are now handled directly by the
route registrar in ``api.rest.admin.registry``.
"""
