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
