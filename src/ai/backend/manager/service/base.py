"""
DEPRECATED: This module is being phased out in favor of ProcessorsCtx pattern.
The registry quota service has been migrated to services/registry_quota/.
"""


class ServicesContext:
    """
    DEPRECATED: This class is being phased out in favor of ProcessorsCtx pattern.

    In the API layer, requests are processed through the ServicesContext and
    its subordinate layers, including the DB, Client, and Repository layers.
    Each layer separates the responsibilities specific to its respective level.
    """

    def __init__(self) -> None:
        pass
