"""Backward-compatibility shim for the logs module.

All error log handler logic has been migrated to:

* ``api.rest.error_log`` — ErrorLogHandler + route registration

The ``PrivateContext`` and lifecycle hooks (``init``/``shutdown``) have been
removed as part of the DependencyComposer migration.  The ``GlobalTimer``
for log cleanup and the event dispatcher integration are now managed
directly by the route registrar in ``api.rest.error_log.registry``.
"""
