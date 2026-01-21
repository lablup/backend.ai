"""Metadata classes for Backend.AI configuration and API documentation.

This package provides metadata classes used for documenting configuration fields
and API DTOs across Backend.AI components.
"""

from .meta import (
    BackendAIAPIMeta,
    BackendAIConfigMeta,
    BackendAIFieldMeta,
    CompositeType,
    ConfigEnvironment,
    ConfigExample,
    generate_composite_example,
    generate_example,
    generate_model_example,
    get_field_meta,
    get_field_type,
)

__all__ = (
    "BackendAIAPIMeta",
    "BackendAIConfigMeta",
    "BackendAIFieldMeta",
    "CompositeType",
    "ConfigEnvironment",
    "ConfigExample",
    "generate_composite_example",
    "generate_example",
    "generate_model_example",
    "get_field_meta",
    "get_field_type",
)
