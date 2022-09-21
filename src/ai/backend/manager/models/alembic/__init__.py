from contextvars import ContextVar

invoked_programmatically = ContextVar("invoked_programmatically", default=False)
