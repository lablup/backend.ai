"""Backward-compatible shim for the spec module.

Documentation-serving handler logic has been migrated to:

* ``api.rest.spec.handler`` — SpecHandler class
* ``api.rest.spec`` — route registration

The lifecycle hook (``init``) has been removed as part of the
DependencyComposer migration.  The OpenAPI introspection warning is
now handled directly by the route registrar in
``api.rest.spec.registry``.
"""
