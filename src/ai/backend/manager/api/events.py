"""Backward-compatibility shim for the events module.

All event streaming handler logic has been migrated to:

* ``api.rest.events.handler`` — EventsHandler class + lifecycle helpers
* ``api.rest.events`` — route registration
"""
