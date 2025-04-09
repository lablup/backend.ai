from aiohttp import web

from ai.backend.common.exception import BackendError


class InvalidAPIParameters(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."


class ModelServiceNotFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/model-service-not-found"
    error_title = "Model service not found."


class GenericForbidden(BackendError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/forbidden"
    error_title = "Forbidden."


class EndpointNotFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/endpoint-not-found"
    error_title = "Endpoint not found."


class EndpointAutoScalingRuleNotFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/endpoint-auto-scaling-rule-not-found"
    error_title = "Endpoint auto scaling rule not found."


class RouteNotFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/route-not-found"
    error_title = "Route not found."
