class PrometheusException(Exception):
    """Base class for Prometheus exceptions."""

    pass


class ResultNotFound(PrometheusException):
    """Exception raised when a Prometheus query returns no results."""
