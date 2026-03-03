"""Backward-compatibility shim for the logs module.

All error log handler logic has been migrated to:

* ``api.rest.error_log`` — ErrorLogHandler + route registration

Lifecycle management has been migrated to the DependencyComposer:

* Event consumer: ``event_dispatcher.handlers.log_cleanup``
* GlobalTimer: ``dependencies.processing.log_cleanup_timer``
"""
