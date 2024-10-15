from __future__ import annotations


class ResourceError(Exception):
    pass


class ResourceLimitExceeded(ResourceError):
    pass
