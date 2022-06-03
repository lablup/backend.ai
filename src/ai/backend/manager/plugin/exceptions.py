"""
This module defines a series of Backend.AI's plugin-specific errors.
"""
from aiohttp import web
from ai.backend.manager.api.exceptions import BackendError


class PluginError(web.HTTPBadRequest, BackendError):
    error_type  = 'https://api.backend.ai/probs/plugin-error'
    error_title = 'Plugin generated error'


class PluginConfigurationError(PluginError):
    error_type  = 'https://api.backend.ai/probs/plugin-config-error'
    error_title = 'Plugin configuration error'
