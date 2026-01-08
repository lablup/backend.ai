from __future__ import annotations

from typing import Annotated

from pydantic import AliasChoices, Field

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.meta import BackendAIConfigMeta, ConfigExample

__all__ = ("PyroscopeConfig",)


class PyroscopeConfig(BaseConfigSchema):
    """Configuration for Pyroscope continuous profiling.

    Pyroscope is used for continuous profiling of Backend.AI components
    to identify performance bottlenecks.
    """

    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Whether to enable Pyroscope profiling. "
                "When enabled, performance profiling data will be sent to a Pyroscope server. "
                "Useful for debugging performance issues, but adds some overhead."
            ),
            added_version="24.12.1",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    app_name: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("app-name", "app_name"),
            serialization_alias="app-name",
        ),
        BackendAIConfigMeta(
            description=(
                "Application name to use in Pyroscope. "
                "This name will identify this component instance in Pyroscope UI. "
                "Required if Pyroscope is enabled."
            ),
            added_version="24.12.1",
            example=ConfigExample(local="backendai-manager", prod="backendai-manager-prod"),
        ),
    ]
    server_addr: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias=AliasChoices("server-addr", "server_addr"),
            serialization_alias="server-addr",
        ),
        BackendAIConfigMeta(
            description=(
                "Address of the Pyroscope server. "
                "Must include the protocol (http or https) and port if non-standard. "
                "Required if Pyroscope is enabled."
            ),
            added_version="24.12.1",
            example=ConfigExample(local="http://localhost:4040", prod="http://pyroscope:4040"),
        ),
    ]
    sample_rate: Annotated[
        int | None,
        Field(
            default=None,
            validation_alias=AliasChoices("sample-rate", "sample_rate"),
            serialization_alias="sample-rate",
        ),
        BackendAIConfigMeta(
            description=(
                "Sampling rate for Pyroscope profiling. "
                "Higher values collect more data but increase overhead. "
                "Balance based on your performance monitoring needs."
            ),
            added_version="24.12.1",
            example=ConfigExample(local="100", prod="100"),
        ),
    ]
