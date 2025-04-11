from ..exceptions import BaseServiceException


class FailedToGetMetric(BaseServiceException):
    """Exception raised when a metric cannot be retrieved."""
