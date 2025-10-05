from __future__ import annotations

import enum
import os
from pathlib import Path
from typing import Optional

from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    FilePath,
    HttpUrl,
    field_validator,
)

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.data.config.types import EtcdConfigData
from ai.backend.common.typed_validators import (
    AutoDirectoryPath,
    CommaSeparatedStrList,
    HostPortPair,
)
from ai.backend.logging.config import LoggingConfig


class ServiceMode(enum.StrEnum):
    WEBUI = "webui"
    STATIC = "static"


class ForceEndpointProtocol(enum.StrEnum):
    HTTPS = "https"
    HTTP = "http"


class WebSocketProxyConfig(BaseConfigSchema):
    url: str = Field(
        default="",
        description="""
        WebSocket proxy URL.
        Used to proxy WebSocket connections through a separate service.
        Leave empty to disable WebSocket proxy.
        """,
        examples=["", "ws://localhost:8080"],
    )


class ServiceConfig(BaseConfigSchema):
    ip: str = Field(
        default="0.0.0.0",
        description="""
        IP address to bind the webserver service.
        Use '0.0.0.0' to bind to all interfaces.
        """,
        examples=["0.0.0.0", "127.0.0.1"],
    )
    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="""
        Port number to bind the webserver service.
        Must be between 1 and 65535.
        """,
        examples=[8080, 8081],
    )
    wsproxy: WebSocketProxyConfig = Field(
        default_factory=WebSocketProxyConfig,
        description="""
        WebSocket proxy configuration.
        """,
    )
    ssl_enabled: bool = Field(
        default=False,
        description="""
        Whether to enable SSL/TLS for the webserver.
        When enabled, requires ssl_cert and ssl_privkey to be set.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("ssl_enabled", "ssl-enabled"),
        serialization_alias="ssl-enabled",
    )
    ssl_cert: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to SSL certificate file.
        Required when ssl_enabled is True.
        """,
        examples=["/path/to/cert.pem"],
        validation_alias=AliasChoices("ssl_cert", "ssl-cert"),
        serialization_alias="ssl-cert",
    )
    ssl_privkey: Optional[FilePath] = Field(
        default=None,
        description="""
        Path to SSL private key file.
        Required when ssl_enabled is True.
        """,
        examples=["/path/to/privkey.pem"],
        validation_alias=AliasChoices("ssl_privkey", "ssl-privkey"),
        serialization_alias="ssl-privkey",
    )
    static_path: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "static",
        description="""
        Path to static files directory.
        Contains web UI assets and other static resources.
        """,
        examples=["/path/to/static"],
        validation_alias=AliasChoices("static_path", "static-path"),
        serialization_alias="static-path",
    )
    force_endpoint_protocol: Optional[ForceEndpointProtocol] = Field(
        default=None,
        description="""
        Force a specific protocol for API endpoints.
        Useful when running behind a reverse proxy.
        """,
        examples=[None, "https", "http"],
        validation_alias=AliasChoices("force_endpoint_protocol", "force-endpoint-protocol"),
        serialization_alias="force-endpoint-protocol",
    )
    mode: ServiceMode = Field(
        default=ServiceMode.WEBUI,
        description="""
        Service mode.
        'webui' serves the full web UI, 'static' serves only static files.
        """,
        examples=["webui", "static"],
    )
    enable_signup: bool = Field(
        default=False,
        description="""
        Whether to enable user signup functionality.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("enable_signup", "enable-signup"),
        serialization_alias="enable-signup",
    )
    allow_anonymous_change_password: bool = Field(
        default=False,
        description="""
        Whether to allow anonymous users to change passwords.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "allow_anonymous_change_password", "allow-anonymous-change-password"
        ),
        serialization_alias="allow-anonymous-change-password",
    )
    allow_project_resource_monitor: bool = Field(
        default=False,
        description="""
        Whether to allow project resource monitoring.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "allow_project_resource_monitor", "allow-project-resource-monitor"
        ),
        serialization_alias="allow-project-resource-monitor",
    )
    allow_change_signin_mode: bool = Field(
        default=False,
        description="""
        Whether to allow users to change signin mode.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("allow_change_signin_mode", "allow-change-signin-mode"),
        serialization_alias="allow-change-signin-mode",
    )
    allow_manual_image_name_for_session: bool = Field(
        default=False,
        description="""
        Whether to allow manual image name specification for sessions.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "allow_manual_image_name_for_session", "allow-manual-image-name-for-session"
        ),
        serialization_alias="allow-manual-image-name-for-session",
    )
    allow_signup_without_confirmation: bool = Field(
        default=False,
        description="""
        Whether to allow signup without email confirmation.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "allow_signup_without_confirmation", "allow-signup-without-confirmation"
        ),
        serialization_alias="allow-signup-without-confirmation",
    )
    always_enqueue_compute_session: bool = Field(
        default=False,
        description="""
        Whether to always enqueue compute sessions.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "always_enqueue_compute_session", "always-enqueue-compute-session"
        ),
        serialization_alias="always-enqueue-compute-session",
    )
    webui_debug: bool = Field(
        default=False,
        description="""
        Whether to enable debug mode for the web UI.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("webui_debug", "webui-debug"),
        serialization_alias="webui-debug",
    )
    mask_user_info: bool = Field(
        default=False,
        description="""
        Whether to mask user information in the UI.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("mask_user_info", "mask-user-info"),
        serialization_alias="mask-user-info",
    )
    single_sign_on_vendors: Optional[CommaSeparatedStrList] = Field(
        default=None,
        description="""
        List of single sign-on vendors to enable.
        """,
        examples=[None, ["google", "github"]],
        validation_alias=AliasChoices("single_sign_on_vendors", "single-sign-on-vendors"),
        serialization_alias="single-sign-on-vendors",
    )
    sso_realm_name: str = Field(
        default="",
        description="""
        SSO realm name for single sign-on.
        """,
        examples=["", "example-realm"],
        validation_alias=AliasChoices("sso_realm_name", "sso-realm-name"),
        serialization_alias="sso-realm-name",
    )
    enable_container_commit: bool = Field(
        default=False,
        description="""
        Whether to enable container commit functionality.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("enable_container_commit", "enable-container-commit"),
        serialization_alias="enable-container-commit",
    )
    hide_agents: bool = Field(
        default=True,
        description="""
        Whether to hide agent information in the UI.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("hide_agents", "hide-agents"),
        serialization_alias="hide-agents",
    )
    app_download_url: str = Field(
        default="",
        description="""
        URL for app download.
        """,
        examples=["", "https://example.com/download"],
        validation_alias=AliasChoices("app_download_url", "app-download-url"),
        serialization_alias="app-download-url",
    )
    allow_app_download_panel: bool = Field(
        default=True,
        description="""
        Whether to allow app download panel in the UI.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("allow_app_download_panel", "allow-app-download-panel"),
        serialization_alias="allow-app-download-panel",
    )
    enable_2fa: bool = Field(
        default=False,
        description="""
        Whether to enable two-factor authentication.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("enable_2FA", "enable-2FA"),
        serialization_alias="enable-2FA",
    )
    force_2fa: bool = Field(
        default=False,
        description="""
        Whether to force two-factor authentication for all users.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("force_2FA", "force-2FA"),
        serialization_alias="force-2FA",
    )
    system_ssh_image: str = Field(
        default="",
        description="""
        System SSH image name.
        """,
        examples=["", "ubuntu:22.04"],
        validation_alias=AliasChoices("system_SSH_image", "system-SSH-image"),
        serialization_alias="system-SSH-image",
    )
    directory_based_usage: bool = Field(
        default=False,
        description="""
        Whether to use directory-based usage tracking.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("directory_based_usage", "directory-based-usage"),
        serialization_alias="directory-based-usage",
    )
    allow_custom_resource_allocation: bool = Field(
        default=True,
        description="""
        Whether to allow custom resource allocation.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "allow_custom_resource_allocation", "allow-custom-resource-allocation"
        ),
        serialization_alias="allow-custom-resource-allocation",
    )
    edu_appname_prefix: str = Field(
        default="",
        description="""
        Education app name prefix.
        """,
        examples=["", "edu-"],
        validation_alias=AliasChoices("edu_appname_prefix", "edu-appname-prefix"),
        serialization_alias="edu-appname-prefix",
    )
    enable_extend_login_session: bool = Field(
        default=False,
        description="""
        Whether to enable extended login sessions.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("enable_extend_login_session", "enable-extend-login-session"),
        serialization_alias="enable-extend-login-session",
    )
    is_directory_size_visible: bool = Field(
        default=True,
        description="""
        Whether directory size is visible in the UI.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("is_directory_size_visible", "is-directory-size-visible"),
        serialization_alias="is-directory-size-visible",
    )
    enable_interactive_login_account_switch: bool = Field(
        default=True,
        description="""
        Whether to enable interactive login account switching.
        """,
        examples=[True, False],
        validation_alias=AliasChoices(
            "enable_interactive_login_account_switch", "enable-interactive-login-account-switch"
        ),
        serialization_alias="enable-interactive-login-account-switch",
    )
    default_file_browser_image: str = Field(
        default="",
        description="""
        Default file browser image name.
        """,
        examples=["", "filebrowser:latest"],
        validation_alias=AliasChoices("default_file_browser_image", "default-file-browser-image"),
        serialization_alias="default-file-browser-image",
    )
    enable_reservoir: bool = Field(
        default=False,
        description="""
        Whether to enable reservoir feature.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("enable_reservoir", "enable-reservoir"),
        serialization_alias="enable-reservoir",
    )

    @field_validator("static_path")
    @classmethod
    def resolve_static_path(cls, v: Path) -> Path:
        return v.resolve()


class CSPConfig(BaseConfigSchema):
    default_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy default-src directive.
        """,
        examples=[None, ["'self'", "https:"]],
        validation_alias=AliasChoices("default_src", "default-src"),
        serialization_alias="default-src",
    )
    connect_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy connect-src directive.
        """,
        examples=[None, ["'self'", "wss:"]],
        validation_alias=AliasChoices("connect_src", "connect-src"),
        serialization_alias="connect-src",
    )
    img_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy img-src directive.
        """,
        examples=[None, ["'self'", "data:"]],
        validation_alias=AliasChoices("img_src", "img-src"),
        serialization_alias="img-src",
    )
    media_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy media-src directive.
        """,
        examples=[None, ["'self'"]],
        validation_alias=AliasChoices("media_src", "media-src"),
        serialization_alias="media-src",
    )
    font_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy font-src directive.
        """,
        examples=[None, ["'self'", "https:"]],
        validation_alias=AliasChoices("font_src", "font-src"),
        serialization_alias="font-src",
    )
    script_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy script-src directive.
        """,
        examples=[None, ["'self'", "'unsafe-inline'"]],
        validation_alias=AliasChoices("script_src", "script-src"),
        serialization_alias="script-src",
    )
    style_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy style-src directive.
        """,
        examples=[None, ["'self'", "'unsafe-inline'"]],
        validation_alias=AliasChoices("style_src", "style-src"),
        serialization_alias="style-src",
    )
    frame_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy frame-src directive.
        """,
        examples=[None, ["'self'"]],
        validation_alias=AliasChoices("frame_src", "frame-src"),
        serialization_alias="frame-src",
    )
    object_src: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy object-src directive.
        """,
        examples=[None, ["'none'"]],
        validation_alias=AliasChoices("object_src", "object-src"),
        serialization_alias="object-src",
    )
    frame_ancestors: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy frame-ancestors directive.
        """,
        examples=[None, ["'self'"]],
        validation_alias=AliasChoices("frame_ancestors", "frame-ancestors"),
        serialization_alias="frame-ancestors",
    )
    form_action: Optional[list[str]] = Field(
        default=None,
        description="""
        Content Security Policy form-action directive.
        """,
        examples=[None, ["'self'"]],
        validation_alias=AliasChoices("form_action", "form-action"),
        serialization_alias="form-action",
    )


class SecurityConfig(BaseConfigSchema):
    request_policies: list[str] = Field(
        default_factory=list,
        description="""
        List of request security policies.
        """,
        examples=[[]],
        validation_alias=AliasChoices("request_policies", "request-policies"),
        serialization_alias="request-policies",
    )
    response_policies: list[str] = Field(
        default_factory=list,
        description="""
        List of response security policies.
        """,
        examples=[[]],
        validation_alias=AliasChoices("response_policies", "response-policies"),
        serialization_alias="response-policies",
    )
    csp: Optional[CSPConfig] = Field(
        default=None,
        description="""
        Content Security Policy configuration.
        """,
        examples=[None],
    )


class ResourcesConfig(BaseConfigSchema):
    open_port_to_public: bool = Field(
        default=False,
        description="""
        Whether to open ports to public.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("open_port_to_public", "open-port-to-public"),
        serialization_alias="open-port-to-public",
    )
    allow_non_auth_tcp: bool = Field(
        default=False,
        description="""
        Whether to allow non-authenticated TCP connections.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("allow_non_auth_tcp", "allow-non-auth-tcp"),
        serialization_alias="allow-non-auth-tcp",
    )
    allow_preferred_port: bool = Field(
        default=False,
        description="""
        Whether to allow preferred port selection.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("allow_preferred_port", "allow-preferred-port"),
        serialization_alias="allow-preferred-port",
    )
    max_cpu_cores_per_container: int = Field(
        default=64,
        description="""
        Maximum CPU cores per container.
        """,
        examples=[64, 128],
        validation_alias=AliasChoices("max_cpu_cores_per_container", "max-cpu-cores-per-container"),
        serialization_alias="max-cpu-cores-per-container",
    )
    max_memory_per_container: int = Field(
        default=64,
        description="""
        Maximum memory per container in GB.
        """,
        examples=[64, 128],
        validation_alias=AliasChoices("max_memory_per_container", "max-memory-per-container"),
        serialization_alias="max-memory-per-container",
    )
    max_cuda_devices_per_container: int = Field(
        default=16,
        description="""
        Maximum CUDA devices per container.
        """,
        examples=[16, 32],
        validation_alias=AliasChoices(
            "max_cuda_devices_per_container", "max-cuda-devices-per-container"
        ),
        serialization_alias="max-cuda-devices-per-container",
    )
    max_cuda_shares_per_container: int = Field(
        default=16,
        description="""
        Maximum CUDA shares per container.
        """,
        examples=[16, 32],
        validation_alias=AliasChoices(
            "max_cuda_shares_per_container", "max-cuda-shares-per-container"
        ),
        serialization_alias="max-cuda-shares-per-container",
    )
    max_rocm_devices_per_container: int = Field(
        default=10,
        description="""
        Maximum ROCm devices per container.
        """,
        examples=[10, 20],
        validation_alias=AliasChoices(
            "max_rocm_devices_per_container", "max-rocm-devices-per-container"
        ),
        serialization_alias="max-rocm-devices-per-container",
    )
    max_tpu_devices_per_container: int = Field(
        default=8,
        description="""
        Maximum TPU devices per container.
        """,
        examples=[8, 16],
        validation_alias=AliasChoices(
            "max_tpu_devices_per_container", "max-tpu-devices-per-container"
        ),
        serialization_alias="max-tpu-devices-per-container",
    )
    max_ipu_devices_per_container: int = Field(
        default=8,
        description="""
        Maximum IPU devices per container.
        """,
        examples=[8, 16],
        validation_alias=AliasChoices(
            "max_ipu_devices_per_container", "max-ipu-devices-per-container"
        ),
        serialization_alias="max-ipu-devices-per-container",
    )
    max_atom_devices_per_container: int = Field(
        default=8,
        description="""
        Maximum Atom devices per container.
        """,
        examples=[8, 16],
        validation_alias=AliasChoices(
            "max_atom_devices_per_container", "max-atom-devices-per-container"
        ),
        serialization_alias="max-atom-devices-per-container",
    )
    max_gaudi2_devices_per_container: int = Field(
        default=8,
        description="""
        Maximum Gaudi2 devices per container.
        """,
        examples=[8, 16],
        validation_alias=AliasChoices(
            "max_gaudi2_devices_per_container", "max-gaudi2-devices-per-container"
        ),
        serialization_alias="max-gaudi2-devices-per-container",
    )
    max_atom_plus_devices_per_container: int = Field(
        default=8,
        description="""
        Maximum Atom Plus devices per container.
        """,
        examples=[8, 16],
        validation_alias=AliasChoices(
            "max_atom_plus_devices_per_container", "max-atom-plus-devices-per-container"
        ),
        serialization_alias="max-atom-plus-devices-per-container",
    )
    max_warboy_devices_per_container: int = Field(
        default=8,
        description="""
        Maximum Warboy devices per container.
        """,
        examples=[8, 16],
        validation_alias=AliasChoices(
            "max_warboy_devices_per_container", "max-warboy-devices-per-container"
        ),
        serialization_alias="max-warboy-devices-per-container",
    )
    max_shm_per_container: float = Field(
        default=2.0,
        description="""
        Maximum shared memory per container in GB.
        """,
        examples=[2.0, 4.0],
        validation_alias=AliasChoices("max_shm_per_container", "max-shm-per-container"),
        serialization_alias="max-shm-per-container",
    )
    max_file_upload_size: int = Field(
        default=4294967296,
        description="""
        Maximum file upload size in bytes.
        """,
        examples=[4294967296, 8589934592],
        validation_alias=AliasChoices("max_file_upload_size", "max-file-upload-size"),
        serialization_alias="max-file-upload-size",
    )


class EnvironmentsConfig(BaseConfigSchema):
    allowlist: Optional[CommaSeparatedStrList] = Field(
        default=None,
        description="""
        List of allowed environments.
        """,
        examples=[None, ["python", "r", "julia"]],
    )
    show_non_installed_images: bool = Field(
        default=False,
        description="""
        Whether to show non-installed images.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("show_non_installed_images", "show-non-installed-images"),
        serialization_alias="show-non-installed-images",
    )


class PluginConfig(BaseConfigSchema):
    page: Optional[CommaSeparatedStrList] = Field(
        default=None,
        description="""
        List of page plugins.
        """,
        examples=[None, ["dashboard", "settings"]],
    )


class PipelineConfig(BaseConfigSchema):
    endpoint: HttpUrl = Field(
        default_factory=lambda: HttpUrl("http://127.0.0.1:9500"),
        description="""
        Pipeline service endpoint URL.
        """,
        examples=["http://127.0.0.1:9500"],
    )
    frontend_endpoint: Optional[str] = Field(
        default=None,
        description="""
        Frontend endpoint URL for pipeline service.
        """,
        examples=[None, "http://127.0.0.1:9501"],
        validation_alias=AliasChoices("frontend_endpoint", "frontend-endpoint"),
        serialization_alias="frontend-endpoint",
    )


class UIConfig(BaseConfigSchema):
    default_environment: Optional[str] = Field(
        default=None,
        description="""
        Default environment for new sessions.
        """,
        examples=[None, "python:3.9-ubuntu20.04"],
        validation_alias=AliasChoices("default_environment", "default-environment"),
        serialization_alias="default-environment",
    )
    default_import_environment: Optional[str] = Field(
        default=None,
        description="""
        Default environment for import operations.
        """,
        examples=[None, "python:3.9-ubuntu20.04"],
        validation_alias=AliasChoices("default_import_environment", "default-import-environment"),
        serialization_alias="default-import-environment",
    )
    menu_blocklist: Optional[CommaSeparatedStrList] = Field(
        default=None,
        description="""
        List of blocked menu items.
        """,
        examples=[None, ["admin", "billing"]],
        validation_alias=AliasChoices("menu_blocklist", "menu-blocklist"),
        serialization_alias="menu-blocklist",
    )
    menu_inactivelist: Optional[CommaSeparatedStrList] = Field(
        default=None,
        description="""
        List of inactive menu items.
        """,
        examples=[None, ["maintenance", "experimental"]],
        validation_alias=AliasChoices("menu_inactivelist", "menu-inactivelist"),
        serialization_alias="menu-inactivelist",
    )
    enable_model_folders: bool = Field(
        default=True,
        description="""
        Whether to enable model folders functionality.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("enable_model_folders", "enable-model-folders"),
        serialization_alias="enable-model-folders",
    )


class APIConfig(BaseConfigSchema):
    domain: str = Field(
        default="default",
        description="""
        API domain name.
        """,
        examples=["api.example.com"],
    )
    endpoint: CommaSeparatedStrList = Field(
        default_factory=lambda: CommaSeparatedStrList("http://127.0.0.1:8080"),
        min_length=1,
        description="""
        API endpoint URL.
        """,
        examples=["http://127.0.0.1:8080,http://api.example.com:8080"],
    )
    text: str = Field(
        default="Backend.AI API",
        description="""
        API text description.
        """,
        examples=["Backend.AI API"],
    )
    ssl_verify: bool = Field(
        default=True,
        description="""
        Whether to verify SSL certificates for API calls.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("ssl_verify", "ssl-verify"),
        serialization_alias="ssl-verify",
    )
    auth_token_name: str = Field(
        default="sToken",
        description="""
        Authentication token name.
        """,
        examples=["sToken", "authToken"],
        validation_alias=AliasChoices("auth_token_name", "auth-token-name"),
        serialization_alias="auth-token-name",
    )
    connection_limit: int = Field(
        default=100,
        ge=1,
        description="""
        Maximum number of simultaneous API connections.
        This limits the number of concurrent API requests that can be processed.
        """,
        examples=[100, 200],
        validation_alias=AliasChoices("connection_limit", "connection-limit"),
        serialization_alias="connection-limit",
    )


class EtcdConfig(BaseConfigSchema):
    namespace: str = Field(
        default="ETCD_NAMESPACE",
        description="""
        Namespace prefix for etcd keys used by Backend.AI.
        Allows multiple Backend.AI clusters to share the same etcd cluster.
        All Backend.AI related keys will be stored under this namespace.
        """,
        examples=["local", "backend"],
    )
    addr: HostPortPair | list[HostPortPair] = Field(
        default=HostPortPair(host="127.0.0.1", port=2379),
        description="""
        Network address of the etcd server.
        Default is the standard etcd port on localhost.
        In production, should point to one or more etcd instance endpoint(s).
        """,
        examples=[
            {"host": "127.0.0.1", "port": 2379},  # single endpoint
            [
                {"host": "127.0.0.4", "port": 2379},
                {"host": "127.0.0.5", "port": 2379},
            ],  # multiple endpoints
        ],
    )
    user: Optional[str] = Field(
        default=None,
        description="""
        Username for authenticating with etcd.
        Optional if etcd doesn't require authentication.
        Should be set along with password for secure deployments.
        """,
        examples=["backend", "manager"],
    )
    password: Optional[str] = Field(
        default=None,
        description="""
        Password for authenticating with etcd.
        Optional if etcd doesn't require authentication.
        Can be a direct password or environment variable reference.
        """,
        examples=["develove", "ETCD_PASSWORD"],
    )

    def to_dataclass(self) -> EtcdConfigData:
        return EtcdConfigData(
            namespace=self.namespace,
            addrs=self.addr if isinstance(self.addr, list) else [self.addr],
            user=self.user,
            password=self.password,
        )


class RedisHelperConfig(BaseConfigSchema):
    socket_timeout: float = Field(
        default=5.0,
        description="""
        Socket timeout in seconds.
        """,
        examples=[5.0, 10.0],
        validation_alias=AliasChoices("socket_timeout", "socket-timeout"),
        serialization_alias="socket_timeout",
    )
    socket_connect_timeout: float = Field(
        default=2.0,
        description="""
        Socket connection timeout in seconds.
        """,
        examples=[2.0, 5.0],
        validation_alias=AliasChoices("socket_connect_timeout", "socket-connect-timeout"),
        serialization_alias="socket_connect_timeout",
    )
    reconnect_poll_timeout: float = Field(
        default=0.3,
        description="""
        Reconnect poll timeout in seconds.
        """,
        examples=[0.3, 1.0],
        validation_alias=AliasChoices("reconnect_poll_timeout", "reconnect-poll-timeout"),
        serialization_alias="reconnect_poll_timeout",
    )


class WebServerRedisConfig(BaseConfigSchema):
    db: int = Field(
        default=0,
        description="""
        Redis database number.
        """,
        examples=[0, 1],
    )


class SessionConfig(BaseConfigSchema):
    redis: RedisConfig = Field(
        default_factory=RedisConfig,
        description="""
        Redis configuration for sessions.
        """,
    )
    max_age: int = Field(
        default=604800,
        description="""
        Session maximum age in seconds.
        """,
        examples=[604800, 1209600],
        validation_alias=AliasChoices("max_age", "max-age"),
        serialization_alias="max-age",
    )
    login_session_extension_sec: Optional[int] = Field(
        default=None,
        description="""
        Login session extension in seconds.
        """,
        examples=[None, 3600],
        validation_alias=AliasChoices("login_session_extension_sec", "login-session-extension-sec"),
        serialization_alias="login-session-extension-sec",
    )
    flush_on_startup: bool = Field(
        default=False,
        description="""
        Whether to flush sessions on startup.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("flush_on_startup", "flush-on-startup"),
        serialization_alias="flush-on-startup",
    )
    login_block_time: int = Field(
        default=1200,
        description="""
        Login block time in seconds.
        """,
        examples=[1200, 3600],
        validation_alias=AliasChoices("login_block_time", "login-block-time"),
        serialization_alias="login-block-time",
    )
    login_allowed_fail_count: int = Field(
        default=10,
        description="""
        Allowed login failure count.
        """,
        examples=[10, 5],
        validation_alias=AliasChoices("login_allowed_fail_count", "login-allowed-fail-count"),
        serialization_alias="login-allowed-fail-count",
    )
    auto_logout: bool = Field(
        default=False,
        description="""
        Whether to enable auto logout.
        """,
        examples=[True, False],
        validation_alias=AliasChoices("auto_logout", "auto-logout"),
        serialization_alias="auto-logout",
    )
    max_count_for_preopen_ports: int = Field(
        default=10,
        description="""
        Maximum count for preopen ports.
        """,
        examples=[10, 20],
        validation_alias=AliasChoices("max_count_for_preopen_ports", "max-count-for-preopen-ports"),
        serialization_alias="max-count-for-preopen-ports",
    )


class LicenseConfig(BaseConfigSchema):
    edition: str = Field(
        default="Open Source",
        description="""
        License edition.
        """,
        examples=["Open Source", "Enterprise"],
    )
    valid_since: str = Field(
        default="",
        description="""
        License valid since date.
        """,
        examples=["", "2023-01-01"],
        validation_alias=AliasChoices("valid_since", "valid-since"),
        serialization_alias="valid-since",
    )
    valid_until: str = Field(
        default="",
        description="""
        License valid until date.
        """,
        examples=["", "2024-01-01"],
        validation_alias=AliasChoices("valid_until", "valid-until"),
        serialization_alias="valid-until",
    )


class EventLoopType(enum.StrEnum):
    asyncio = "asyncio"
    uvloop = "uvloop"


class WebServerConfig(BaseConfigSchema):
    event_loop: EventLoopType = Field(
        default=EventLoopType.uvloop,
        description="""
        Event loop type.
        """,
        examples=["asyncio", "uvloop"],
        validation_alias=AliasChoices("event_loop", "event-loop"),
        serialization_alias="event-loop",
    )
    ipc_base_path: AutoDirectoryPath = Field(
        default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
        description="""
        IPC base path.
        """,
        examples=["/tmp/backend.ai/ipc"],
        validation_alias=AliasChoices("ipc_base_path", "ipc-base-path"),
        serialization_alias="ipc-base-path",
    )
    pid_file: Path = Field(
        default=Path(os.devnull),
        description="""
        Process ID file path.
        """,
        examples=["/var/run/webserver.pid"],
        validation_alias=AliasChoices("pid_file", "pid-file"),
        serialization_alias="pid-file",
    )


class LogLevel(enum.StrEnum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class OTELConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="""
        Whether to enable OpenTelemetry.
        """,
        examples=[True, False],
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="""
        OpenTelemetry log level.
        """,
        examples=["INFO", "DEBUG"],
        validation_alias=AliasChoices("log_level", "log-level"),
        serialization_alias="log-level",
    )
    endpoint: str = Field(
        default="http://127.0.0.1:4317",
        description="""
        OpenTelemetry endpoint.
        """,
        examples=["http://127.0.0.1:4317"],
    )


class ApolloRouterConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="""
        Whether to enable Apollo Router.
        """,
        examples=[True, False],
    )
    endpoint: str = Field(
        default="http://127.0.0.1:4000",
        description="""
        Apollo Router endpoint.
        """,
        examples=["http://127.0.0.1:4000"],
    )


class DebugConfig(BaseConfigSchema):
    enabled: bool = Field(
        default=False,
        description="""
        Whether to enable debug mode.
        """,
        examples=[True, False],
    )


class WebServerUnifiedConfig(BaseConfigSchema):
    service: ServiceConfig = Field(
        default_factory=ServiceConfig,
        description="""
        Service configuration.
        """,
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="""
        Security configuration.
        """,
    )
    resources: ResourcesConfig = Field(
        default_factory=ResourcesConfig,
        description="""
        Resources configuration.
        """,
    )
    environments: EnvironmentsConfig = Field(
        default_factory=EnvironmentsConfig,
        description="""
        Environments configuration.
        """,
    )
    plugin: PluginConfig = Field(
        default_factory=PluginConfig,
        description="""
        Plugin configuration.
        """,
    )
    pipeline: PipelineConfig = Field(
        default_factory=PipelineConfig,
        description="""
        Pipeline configuration.
        """,
    )
    ui: UIConfig = Field(
        default_factory=UIConfig,
        description="""
        UI configuration.
        """,
    )
    api: APIConfig = Field(
        default_factory=APIConfig,
        description="""
        API configuration.
        """,
    )
    session: SessionConfig = Field(
        default_factory=SessionConfig,
        description="""
        Session configuration.
        """,
    )
    license: LicenseConfig = Field(
        default_factory=LicenseConfig,
        description="""
        License configuration.
        """,
    )
    webserver: WebServerConfig = Field(
        default_factory=WebServerConfig,
        description="""
        Web server configuration.
        """,
    )
    otel: OTELConfig = Field(
        default_factory=OTELConfig,
        description="""
        OpenTelemetry configuration.
        """,
    )
    apollo_router: ApolloRouterConfig = Field(
        default_factory=ApolloRouterConfig,
        description="""
        Apollo Router configuration.
        """,
        validation_alias=AliasChoices("apollo_router", "apollo-router"),
        serialization_alias="sapollo-router",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="""
        Logging configuration.
        """,
    )
    debug: DebugConfig = Field(
        default_factory=DebugConfig,
        description="""
        Debug configuration.
        """,
    )

    # TODO: Remove me after changing config injection logic
    model_config = ConfigDict(
        extra="allow",
    )
