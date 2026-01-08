from __future__ import annotations

import enum
import os
from pathlib import Path
from typing import Annotated, Optional

from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    FilePath,
    HttpUrl,
    field_validator,
)

from ai.backend.common.config import BaseConfigSchema
from ai.backend.common.configs import (
    EtcdConfig,
    OTELConfig,
    PyroscopeConfig,
    ServiceDiscoveryConfig,
)
from ai.backend.common.configs.jwt import SharedJWTConfig
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.meta import BackendAIConfigMeta, CompositeType, ConfigExample
from ai.backend.common.typed_validators import (
    AutoDirectoryPath,
    CommaSeparatedStrList,
)
from ai.backend.logging.config import LoggingConfig


class ServiceMode(enum.StrEnum):
    WEBUI = "webui"
    STATIC = "static"


class ForceEndpointProtocol(enum.StrEnum):
    HTTPS = "https"
    HTTP = "http"


class WebSocketProxyConfig(BaseConfigSchema):
    url: Annotated[
        str,
        Field(default=""),
        BackendAIConfigMeta(
            description=(
                "WebSocket proxy URL for routing WebSocket connections through a separate "
                "proxy service. Used when the webserver needs to forward WebSocket traffic "
                "to another service. Leave empty to disable WebSocket proxying."
            ),
            added_version="25.12.0",
            example=ConfigExample(
                local="ws://localhost:8080", prod="ws://wsproxy.example.com:8080"
            ),
        ),
    ]


class ServiceConfig(BaseConfigSchema):
    ip: Annotated[
        str,
        Field(default="0.0.0.0"),
        BackendAIConfigMeta(
            description=(
                "IP address to bind the webserver service. Use '0.0.0.0' to listen on all "
                "network interfaces (recommended for production), or '127.0.0.1' to restrict "
                "to localhost only (useful for development or when behind a reverse proxy)."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="127.0.0.1", prod="0.0.0.0"),
        ),
    ]
    port: Annotated[
        int,
        Field(default=8080, ge=1, le=65535),
        BackendAIConfigMeta(
            description=(
                "Port number to bind the webserver service. Standard HTTP is 80, HTTPS is 443. "
                "Use high ports (>1024) to run without root privileges. Common alternatives "
                "include 8080, 8443, or 3000."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="8080", prod="8080"),
        ),
    ]
    wsproxy: Annotated[
        WebSocketProxyConfig,
        Field(default_factory=WebSocketProxyConfig),
        BackendAIConfigMeta(
            description=(
                "WebSocket proxy configuration for routing WebSocket connections. Configure "
                "this when you need to proxy WebSocket traffic through a separate service, "
                "typically for terminal and interactive app connections."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    ssl_enabled: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("ssl_enabled", "ssl-enabled"),
            serialization_alias="ssl-enabled",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable SSL/TLS encryption for the webserver. When enabled, all HTTP "
                "connections are served over HTTPS. Requires ssl_cert and ssl_privkey to be "
                "configured. Strongly recommended for production deployments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    ssl_cert: Annotated[
        Optional[FilePath],
        Field(
            default=None,
            validation_alias=AliasChoices("ssl_cert", "ssl-cert"),
            serialization_alias="ssl-cert",
        ),
        BackendAIConfigMeta(
            description=(
                "File path to the SSL/TLS certificate in PEM format. Required when ssl_enabled "
                "is true. Should contain the full certificate chain including intermediate "
                "certificates for proper validation by browsers."
            ),
            added_version="25.12.0",
            example=ConfigExample(
                local="fixtures/webserver/webserver.crt", prod="/etc/ssl/certs/webserver.crt"
            ),
        ),
    ]
    ssl_privkey: Annotated[
        Optional[FilePath],
        Field(
            default=None,
            validation_alias=AliasChoices("ssl_privkey", "ssl-privkey"),
            serialization_alias="ssl-privkey",
        ),
        BackendAIConfigMeta(
            description=(
                "File path to the SSL/TLS private key in PEM format. Required when ssl_enabled "
                "is true. Keep this file secure with restricted permissions (e.g., 0600) and "
                "never share or commit to version control."
            ),
            added_version="25.12.0",
            secret=True,
        ),
    ]
    static_path: Annotated[
        Path,
        Field(
            default_factory=lambda: Path(__file__).parent.parent / "static",
            validation_alias=AliasChoices("static_path", "static-path"),
            serialization_alias="static-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Directory path containing static web assets (HTML, CSS, JavaScript, images). "
                "The webserver serves these files directly to browsers. Defaults to the bundled "
                "static directory within the package."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="./static", prod="/var/www/backend.ai/static"),
        ),
    ]
    force_endpoint_protocol: Annotated[
        Optional[ForceEndpointProtocol],
        Field(
            default=None,
            validation_alias=AliasChoices("force_endpoint_protocol", "force-endpoint-protocol"),
            serialization_alias="force-endpoint-protocol",
        ),
        BackendAIConfigMeta(
            description=(
                "Force a specific protocol (http or https) for generated API endpoint URLs. "
                "Useful when running behind a reverse proxy that terminates SSL. Set to "
                "'https' if the proxy handles SSL but the webserver runs on HTTP."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="http", prod="https"),
        ),
    ]
    mode: Annotated[
        ServiceMode,
        Field(default=ServiceMode.WEBUI),
        BackendAIConfigMeta(
            description=(
                "Service operation mode. 'webui' serves the full Backend.AI web interface with "
                "all features. 'static' serves only static files, useful for CDN or custom "
                "frontend deployments that don't need the built-in UI."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="webui", prod="webui"),
        ),
    ]
    enable_signup: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("enable_signup", "enable-signup"),
            serialization_alias="enable-signup",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable user self-registration through the web interface. When disabled, only "
                "administrators can create new user accounts. Enable for public-facing "
                "deployments that allow self-service signup."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    allow_anonymous_change_password: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "allow_anonymous_change_password", "allow-anonymous-change-password"
            ),
            serialization_alias="allow-anonymous-change-password",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow password changes without requiring current authentication. Useful for "
                "password reset flows where users have forgotten their password. Enable with "
                "caution as it may reduce security."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    allow_project_resource_monitor: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "allow_project_resource_monitor", "allow-project-resource-monitor"
            ),
            serialization_alias="allow-project-resource-monitor",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable project-level resource monitoring in the web UI. Shows aggregated "
                "resource usage statistics per project (group). Useful for project managers "
                "to track their team's resource consumption."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    allow_change_signin_mode: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("allow_change_signin_mode", "allow-change-signin-mode"),
            serialization_alias="allow-change-signin-mode",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow users to switch between different sign-in methods (e.g., password, SSO). "
                "When disabled, users must use the sign-in method configured by the administrator."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    allow_manual_image_name_for_session: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "allow_manual_image_name_for_session", "allow-manual-image-name-for-session"
            ),
            serialization_alias="allow-manual-image-name-for-session",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow users to manually specify container image names when creating sessions. "
                "Useful for advanced users who need to use custom or unlisted images. "
                "Disable for controlled environments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    allow_signup_without_confirmation: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "allow_signup_without_confirmation", "allow-signup-without-confirmation"
            ),
            serialization_alias="allow-signup-without-confirmation",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow user accounts to be activated immediately upon registration without "
                "email confirmation. Enable for internal deployments where email verification "
                "is not required. Disable for public-facing services."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    always_enqueue_compute_session: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "always_enqueue_compute_session", "always-enqueue-compute-session"
            ),
            serialization_alias="always-enqueue-compute-session",
        ),
        BackendAIConfigMeta(
            description=(
                "Force all compute session requests to go through the scheduling queue. "
                "When disabled, sessions may start immediately if resources are available. "
                "Enable for fair resource allocation in multi-user environments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    webui_debug: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("webui_debug", "webui-debug"),
            serialization_alias="webui-debug",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable debug mode for the web UI frontend. Shows additional debugging "
                "information in the browser console and may expose internal state. "
                "Should be disabled in production for security."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    mask_user_info: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("mask_user_info", "mask-user-info"),
            serialization_alias="mask-user-info",
        ),
        BackendAIConfigMeta(
            description=(
                "Mask sensitive user information (email, full name) in the UI for privacy. "
                "Shows partial or redacted information instead of full details. Useful for "
                "compliance with privacy regulations."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    single_sign_on_vendors: Annotated[
        Optional[CommaSeparatedStrList],
        Field(
            default=None,
            validation_alias=AliasChoices("single_sign_on_vendors", "single-sign-on-vendors"),
            serialization_alias="single-sign-on-vendors",
        ),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of enabled SSO providers (e.g., 'google,github,keycloak'). "
                "Each provider must be separately configured in the Manager. Set to None to "
                "disable SSO and use only local authentication."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="google", prod="google,keycloak"),
        ),
    ]
    sso_realm_name: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("sso_realm_name", "sso-realm-name"),
            serialization_alias="sso-realm-name",
        ),
        BackendAIConfigMeta(
            description=(
                "SSO realm name for identity providers that use realms (e.g., Keycloak). "
                "Identifies the authentication realm within the SSO provider. Leave empty "
                "if not using realm-based SSO."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="backend-ai-dev", prod="backend-ai"),
        ),
    ]
    enable_container_commit: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("enable_container_commit", "enable-container-commit"),
            serialization_alias="enable-container-commit",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable container commit functionality that allows users to save their "
                "session environments as new container images. Useful for preserving custom "
                "environments but requires additional storage and image management."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    hide_agents: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("hide_agents", "hide-agents"),
            serialization_alias="hide-agents",
        ),
        BackendAIConfigMeta(
            description=(
                "Hide compute agent information from regular users in the UI. When enabled, "
                "users cannot see which physical machines their sessions run on. Enable for "
                "security and simplified user experience."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    app_download_url: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("app_download_url", "app-download-url"),
            serialization_alias="app-download-url",
        ),
        BackendAIConfigMeta(
            description=(
                "URL for downloading Backend.AI desktop applications or CLI tools. "
                "Shown in the app download panel if enabled. Leave empty to hide "
                "the download link."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="https://releases.example.com/backend-ai"),
        ),
    ]
    allow_app_download_panel: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("allow_app_download_panel", "allow-app-download-panel"),
            serialization_alias="allow-app-download-panel",
        ),
        BackendAIConfigMeta(
            description=(
                "Show the application download panel in the web UI. The panel provides "
                "links to download Backend.AI desktop apps and CLI tools. Disable if "
                "you don't want users to see download options."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    enable_2fa: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("enable_2FA", "enable-2FA"),
            serialization_alias="enable-2FA",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable two-factor authentication (2FA) support. When enabled, users can "
                "optionally set up TOTP-based 2FA for enhanced account security. "
                "Requires proper 2FA configuration in the Manager."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    force_2fa: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("force_2FA", "force-2FA"),
            serialization_alias="force-2FA",
        ),
        BackendAIConfigMeta(
            description=(
                "Require all users to set up two-factor authentication. Users who haven't "
                "configured 2FA will be prompted to do so before accessing the system. "
                "Requires enable_2fa to be true."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    system_ssh_image: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("system_SSH_image", "system-SSH-image"),
            serialization_alias="system-SSH-image",
        ),
        BackendAIConfigMeta(
            description=(
                "Default container image for system SSH access sessions. Specifies which "
                "image to use when users request SSH access to the system. Leave empty "
                "to use the default system image."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="cr.backend.ai/system/ssh:latest"),
        ),
    ]
    directory_based_usage: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("directory_based_usage", "directory-based-usage"),
            serialization_alias="directory-based-usage",
        ),
        BackendAIConfigMeta(
            description=(
                "Track resource usage based on directory structure. When enabled, usage "
                "statistics are calculated per directory/project hierarchy rather than "
                "flat aggregation. Useful for organizational billing."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    allow_custom_resource_allocation: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices(
                "allow_custom_resource_allocation", "allow-custom-resource-allocation"
            ),
            serialization_alias="allow-custom-resource-allocation",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow users to customize resource allocation (CPU, memory, GPU) when "
                "creating sessions. When disabled, users must choose from predefined "
                "resource templates. Disable for simplified user experience."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    edu_appname_prefix: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("edu_appname_prefix", "edu-appname-prefix"),
            serialization_alias="edu-appname-prefix",
        ),
        BackendAIConfigMeta(
            description=(
                "Prefix for educational application names. Used to identify and filter "
                "applications meant for educational environments. Leave empty to disable "
                "educational app filtering."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="edu-"),
        ),
    ]
    enable_extend_login_session: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices(
                "enable_extend_login_session", "enable-extend-login-session"
            ),
            serialization_alias="enable-extend-login-session",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow users to extend their login session beyond the default timeout. "
                "When enabled, users can request session extension before automatic logout. "
                "Useful for long-running work without frequent re-authentication."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    is_directory_size_visible: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("is_directory_size_visible", "is-directory-size-visible"),
            serialization_alias="is-directory-size-visible",
        ),
        BackendAIConfigMeta(
            description=(
                "Show directory sizes in the file browser. When disabled, directory sizes "
                "are not calculated, which can improve performance for large directory "
                "trees but provides less information to users."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    enable_interactive_login_account_switch: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices(
                "enable_interactive_login_account_switch", "enable-interactive-login-account-switch"
            ),
            serialization_alias="enable-interactive-login-account-switch",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow users to switch between multiple accounts during an interactive session. "
                "Useful for users who manage multiple projects or have admin/user dual roles. "
                "Disable for simpler single-account workflows."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]
    default_file_browser_image: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices(
                "default_file_browser_image", "default-file-browser-image"
            ),
            serialization_alias="default-file-browser-image",
        ),
        BackendAIConfigMeta(
            description=(
                "Default container image for the file browser application. Specifies which "
                "image to use when users open the built-in file browser. Leave empty to "
                "use the system default."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="cr.backend.ai/filebrowser:latest"),
        ),
    ]
    enable_reservoir: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("enable_reservoir", "enable-reservoir"),
            serialization_alias="enable-reservoir",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable the Reservoir feature for managing ML model artifacts. Reservoir "
                "provides model versioning, sharing, and deployment capabilities. "
                "Requires storage-proxy Reservoir configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]

    @field_validator("static_path")
    @classmethod
    def resolve_static_path(cls, v: Path) -> Path:
        return v.resolve()


class CSPConfig(BaseConfigSchema):
    """Content Security Policy (CSP) configuration.

    CSP is a security standard that helps prevent cross-site scripting (XSS),
    clickjacking, and other code injection attacks by controlling which resources
    the browser is allowed to load.
    """

    default_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("default_src", "default-src"),
            serialization_alias="default-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP default-src directive. Serves as the fallback for other resource types "
                "when their specific directive is not set. Common values include \"'self'\" "
                "(same origin only), \"'none'\" (block all), or specific domains."
            ),
            added_version="25.12.0",
        ),
    ]
    connect_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("connect_src", "connect-src"),
            serialization_alias="connect-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP connect-src directive. Controls which URLs can be loaded using script "
                "interfaces like fetch, XMLHttpRequest, and WebSocket. Essential for API calls "
                'and WebSocket connections. Include "wss:" for WebSocket support.'
            ),
            added_version="25.12.0",
        ),
    ]
    img_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("img_src", "img-src"),
            serialization_alias="img-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP img-src directive. Specifies valid sources for images and favicons. "
                'Include "data:" to allow inline data URIs for images, which is common for '
                "dynamically generated or embedded images."
            ),
            added_version="25.12.0",
        ),
    ]
    media_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("media_src", "media-src"),
            serialization_alias="media-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP media-src directive. Specifies valid sources for loading audio and video "
                "elements. Set to \"'self'\" to only allow media from the same origin, "
                "or include specific CDN domains."
            ),
            added_version="25.12.0",
        ),
    ]
    font_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("font_src", "font-src"),
            serialization_alias="font-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP font-src directive. Defines valid sources for fonts loaded using @font-face. "
                "Include font CDN domains like Google Fonts or self-hosted font locations."
            ),
            added_version="25.12.0",
        ),
    ]
    script_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("script_src", "script-src"),
            serialization_alias="script-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP script-src directive. Specifies valid sources for JavaScript. "
                "\"'unsafe-inline'\" allows inline scripts (less secure but often required). "
                "\"'strict-dynamic'\" can be used with nonces for better security."
            ),
            added_version="25.12.0",
        ),
    ]
    style_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("style_src", "style-src"),
            serialization_alias="style-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP style-src directive. Specifies valid sources for stylesheets. "
                "\"'unsafe-inline'\" is often needed for frameworks that inject styles dynamically. "
                "Consider using hashes or nonces for stricter security."
            ),
            added_version="25.12.0",
        ),
    ]
    frame_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("frame_src", "frame-src"),
            serialization_alias="frame-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP frame-src directive. Specifies valid sources for nested browsing contexts "
                "using <frame> and <iframe>. Important for embedded content like Jupyter notebooks "
                "or app proxies."
            ),
            added_version="25.12.0",
        ),
    ]
    object_src: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("object_src", "object-src"),
            serialization_alias="object-src",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP object-src directive. Specifies valid sources for <object>, <embed>, "
                "and <applet> elements. Typically set to \"'none'\" as these elements are "
                "rarely needed and can be security risks."
            ),
            added_version="25.12.0",
        ),
    ]
    frame_ancestors: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("frame_ancestors", "frame-ancestors"),
            serialization_alias="frame-ancestors",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP frame-ancestors directive. Specifies valid parents that may embed a page "
                "using <frame>, <iframe>, or <object>. Replaces the X-Frame-Options header. "
                "Set to \"'none'\" to prevent any embedding (clickjacking protection)."
            ),
            added_version="25.12.0",
        ),
    ]
    form_action: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            validation_alias=AliasChoices("form_action", "form-action"),
            serialization_alias="form-action",
        ),
        BackendAIConfigMeta(
            description=(
                "CSP form-action directive. Restricts URLs which can be used as form submission "
                "targets. Set to \"'self'\" to only allow form submissions to the same origin, "
                "preventing form hijacking attacks."
            ),
            added_version="25.12.0",
        ),
    ]


class SecurityConfig(BaseConfigSchema):
    """Security configuration for the web server.

    Provides settings for HTTP security policies including Content Security Policy (CSP),
    request/response middleware policies, and other browser security headers.
    """

    request_policies: Annotated[
        list[str],
        Field(
            default_factory=list,
            validation_alias=AliasChoices("request_policies", "request-policies"),
            serialization_alias="request-policies",
        ),
        BackendAIConfigMeta(
            description=(
                "List of request security policy names to apply. These policies are processed "
                "as middleware on incoming requests. Common policies include CORS handling, "
                "request size limits, and rate limiting. Empty list means no additional policies."
            ),
            added_version="25.12.0",
        ),
    ]
    response_policies: Annotated[
        list[str],
        Field(
            default_factory=list,
            validation_alias=AliasChoices("response_policies", "response-policies"),
            serialization_alias="response-policies",
        ),
        BackendAIConfigMeta(
            description=(
                "List of response security policy names to apply. These policies are processed "
                "as middleware on outgoing responses. Can include security headers like "
                "X-Content-Type-Options, X-Frame-Options, etc. Empty list means no additional policies."
            ),
            added_version="25.12.0",
        ),
    ]
    csp: Annotated[
        Optional[CSPConfig],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Content Security Policy configuration. When set, adds CSP headers to responses "
                "to protect against XSS and other injection attacks. Leave unset (None) to skip "
                "CSP headers entirely."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]


class ResourcesConfig(BaseConfigSchema):
    """Resource limits and capabilities for the web UI.

    Defines maximum resource allocations that users can request through the web interface,
    including CPU, memory, accelerators, and network features.
    """

    open_port_to_public: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("open_port_to_public", "open-port-to-public"),
            serialization_alias="open-port-to-public",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow users to open container ports to the public internet. When enabled, "
                "users can expose their container services to external access. Disable for "
                "security-restricted environments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    allow_non_auth_tcp: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("allow_non_auth_tcp", "allow-non-auth-tcp"),
            serialization_alias="allow-non-auth-tcp",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow non-authenticated TCP connections to container services. When disabled, "
                "all TCP connections require authentication through the app proxy. Enable only "
                "for trusted network environments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    allow_preferred_port: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("allow_preferred_port", "allow-preferred-port"),
            serialization_alias="allow-preferred-port",
        ),
        BackendAIConfigMeta(
            description=(
                "Allow users to specify preferred port numbers for their services. "
                "When disabled, ports are automatically assigned. Enable to give users "
                "more control over service accessibility."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    max_cpu_cores_per_container: Annotated[
        int,
        Field(
            default=64,
            validation_alias=AliasChoices(
                "max_cpu_cores_per_container", "max-cpu-cores-per-container"
            ),
            serialization_alias="max-cpu-cores-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of CPU cores a single container can request. This is a "
                "UI-level limit shown to users. Actual allocation depends on resource "
                "policies and agent availability."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="8", prod="64"),
        ),
    ]
    max_memory_per_container: Annotated[
        int,
        Field(
            default=64,
            validation_alias=AliasChoices("max_memory_per_container", "max-memory-per-container"),
            serialization_alias="max-memory-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum memory in gigabytes (GB) a single container can request. This is "
                "a UI-level limit. Actual allocation depends on resource policies and agent "
                "availability."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="16", prod="64"),
        ),
    ]
    max_cuda_devices_per_container: Annotated[
        int,
        Field(
            default=16,
            validation_alias=AliasChoices(
                "max_cuda_devices_per_container", "max-cuda-devices-per-container"
            ),
            serialization_alias="max-cuda-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of NVIDIA CUDA GPU devices a single container can request. "
                "Applies to both full GPU allocation and MIG (Multi-Instance GPU) partitions. "
                "Set based on your largest GPU node configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="16"),
        ),
    ]
    max_cuda_shares_per_container: Annotated[
        int,
        Field(
            default=16,
            validation_alias=AliasChoices(
                "max_cuda_shares_per_container", "max-cuda-shares-per-container"
            ),
            serialization_alias="max-cuda-shares-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of CUDA shares (fractional GPU) a single container can request. "
                "Used with GPU sharing/virtualization solutions like CUDA MPS or vGPU. "
                "Each share represents a fraction of GPU resources."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="16"),
        ),
    ]
    max_rocm_devices_per_container: Annotated[
        int,
        Field(
            default=10,
            validation_alias=AliasChoices(
                "max_rocm_devices_per_container", "max-rocm-devices-per-container"
            ),
            serialization_alias="max-rocm-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of AMD ROCm GPU devices a single container can request. "
                "Applies to AMD Instinct and Radeon Pro GPUs. Set based on your largest "
                "AMD GPU node configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="10"),
        ),
    ]
    max_tpu_devices_per_container: Annotated[
        int,
        Field(
            default=8,
            validation_alias=AliasChoices(
                "max_tpu_devices_per_container", "max-tpu-devices-per-container"
            ),
            serialization_alias="max-tpu-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of Google TPU (Tensor Processing Unit) devices a single "
                "container can request. TPUs are specialized for machine learning workloads. "
                "Set based on your TPU pod configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="8"),
        ),
    ]
    max_ipu_devices_per_container: Annotated[
        int,
        Field(
            default=8,
            validation_alias=AliasChoices(
                "max_ipu_devices_per_container", "max-ipu-devices-per-container"
            ),
            serialization_alias="max-ipu-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of Graphcore IPU (Intelligence Processing Unit) devices a "
                "single container can request. IPUs are optimized for machine intelligence "
                "workloads. Set based on your IPU-POD configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="8"),
        ),
    ]
    max_atom_devices_per_container: Annotated[
        int,
        Field(
            default=8,
            validation_alias=AliasChoices(
                "max_atom_devices_per_container", "max-atom-devices-per-container"
            ),
            serialization_alias="max-atom-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of Rebellions ATOM accelerator devices a single container "
                "can request. ATOM is an AI accelerator for inference workloads. Set based "
                "on your node configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="8"),
        ),
    ]
    max_gaudi2_devices_per_container: Annotated[
        int,
        Field(
            default=8,
            validation_alias=AliasChoices(
                "max_gaudi2_devices_per_container", "max-gaudi2-devices-per-container"
            ),
            serialization_alias="max-gaudi2-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of Intel Gaudi2 accelerator devices a single container "
                "can request. Gaudi2 is optimized for deep learning training and inference. "
                "Set based on your HLS-Gaudi2 server configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="8"),
        ),
    ]
    max_atom_plus_devices_per_container: Annotated[
        int,
        Field(
            default=8,
            validation_alias=AliasChoices(
                "max_atom_plus_devices_per_container", "max-atom-plus-devices-per-container"
            ),
            serialization_alias="max-atom-plus-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of Rebellions ATOM+ accelerator devices a single container "
                "can request. ATOM+ is an enhanced AI accelerator with improved performance. "
                "Set based on your node configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="8"),
        ),
    ]
    max_warboy_devices_per_container: Annotated[
        int,
        Field(
            default=8,
            validation_alias=AliasChoices(
                "max_warboy_devices_per_container", "max-warboy-devices-per-container"
            ),
            serialization_alias="max-warboy-devices-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of FuriosaAI Warboy accelerator devices a single container "
                "can request. Warboy is an NPU optimized for vision and language AI workloads. "
                "Set based on your node configuration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="1", prod="8"),
        ),
    ]
    max_shm_per_container: Annotated[
        float,
        Field(
            default=2.0,
            validation_alias=AliasChoices("max_shm_per_container", "max-shm-per-container"),
            serialization_alias="max-shm-per-container",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum shared memory (/dev/shm) size in gigabytes (GB) a container can request. "
                "Shared memory is used for inter-process communication and some ML frameworks "
                "like PyTorch DataLoader."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="2.0", prod="4.0"),
        ),
    ]
    max_file_upload_size: Annotated[
        int,
        Field(
            default=4294967296,
            validation_alias=AliasChoices("max_file_upload_size", "max-file-upload-size"),
            serialization_alias="max-file-upload-size",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum file upload size in bytes. Default is 4GB (4294967296 bytes). "
                "This limit applies to file uploads through the web interface. Large file "
                "uploads may require increased server timeouts."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="4294967296", prod="4294967296"),
        ),
    ]


class EnvironmentsConfig(BaseConfigSchema):
    """Configuration for container image environments displayed in the UI.

    Controls which container images are visible to users and how they are presented.
    """

    allowlist: Annotated[
        Optional[CommaSeparatedStrList],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of allowed environment image name patterns to display. "
                "When set, only images matching these patterns are shown to users. "
                "Leave empty (None) to show all available images."
            ),
            added_version="25.12.0",
        ),
    ]
    show_non_installed_images: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("show_non_installed_images", "show-non-installed-images"),
            serialization_alias="show-non-installed-images",
        ),
        BackendAIConfigMeta(
            description=(
                "Show container images that are available but not yet installed on agents. "
                "When enabled, users can see and request images that will be pulled on demand. "
                "Disable to only show pre-installed images."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]


class PluginConfig(BaseConfigSchema):
    """Configuration for web UI plugins.

    Allows customization of the web interface through plugin pages.
    """

    page: Annotated[
        Optional[CommaSeparatedStrList],
        Field(default=None),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of plugin page names to load in the UI. "
                "Plugin pages extend the web interface with custom functionality. "
                "Leave empty (None) to disable all page plugins."
            ),
            added_version="25.12.0",
        ),
    ]


class PipelineConfig(BaseConfigSchema):
    """Configuration for Backend.AI Pipeline service integration.

    Pipeline service provides ML workflow automation and experiment tracking.
    """

    endpoint: Annotated[
        HttpUrl,
        Field(default_factory=lambda: HttpUrl("http://127.0.0.1:9500")),
        BackendAIConfigMeta(
            description=(
                "Backend URL of the Pipeline service API. The web server proxies pipeline "
                "requests to this endpoint. Use internal cluster DNS or IP in Kubernetes."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="http://127.0.0.1:9500", prod="http://pipeline-api:9500"),
        ),
    ]
    frontend_endpoint: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("frontend_endpoint", "frontend-endpoint"),
            serialization_alias="frontend-endpoint",
        ),
        BackendAIConfigMeta(
            description=(
                "External URL for the Pipeline frontend. If different from the main endpoint, "
                "set this for users to access the Pipeline UI directly. Leave empty if Pipeline "
                "UI is accessed through the main web interface."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="https://pipeline.example.com"),
        ),
    ]


class UIConfig(BaseConfigSchema):
    """Configuration for web UI customization.

    Controls default behaviors, menu visibility, and feature toggles in the user interface.
    """

    default_environment: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices("default_environment", "default-environment"),
            serialization_alias="default-environment",
        ),
        BackendAIConfigMeta(
            description=(
                "Default container image pre-selected when users create new compute sessions. "
                "Specify a full image name like 'python:3.9-ubuntu20.04'. Leave empty to let "
                "users choose from available images."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="cr.backend.ai/python:3.10-ubuntu22.04"),
        ),
    ]
    default_import_environment: Annotated[
        Optional[str],
        Field(
            default=None,
            validation_alias=AliasChoices(
                "default_import_environment", "default-import-environment"
            ),
            serialization_alias="default-import-environment",
        ),
        BackendAIConfigMeta(
            description=(
                "Default container image for import operations like folder uploads or "
                "Git repository cloning. Typically set to a lightweight Python image "
                "with common data tools."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="cr.backend.ai/python:3.10-ubuntu22.04"),
        ),
    ]
    menu_blocklist: Annotated[
        Optional[CommaSeparatedStrList],
        Field(
            default=None,
            validation_alias=AliasChoices("menu_blocklist", "menu-blocklist"),
            serialization_alias="menu-blocklist",
        ),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of menu items to completely hide from all users. "
                "Blocked menus are removed from the UI and cannot be accessed. "
                "Use for features not available in your deployment."
            ),
            added_version="25.12.0",
        ),
    ]
    menu_inactivelist: Annotated[
        Optional[CommaSeparatedStrList],
        Field(
            default=None,
            validation_alias=AliasChoices("menu_inactivelist", "menu-inactivelist"),
            serialization_alias="menu-inactivelist",
        ),
        BackendAIConfigMeta(
            description=(
                "Comma-separated list of menu items to show as inactive (grayed out). "
                "Inactive menus are visible but not clickable. Use for features coming soon "
                "or temporarily disabled."
            ),
            added_version="25.12.0",
        ),
    ]
    enable_model_folders: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("enable_model_folders", "enable-model-folders"),
            serialization_alias="enable-model-folders",
        ),
        BackendAIConfigMeta(
            description=(
                "Enable the model folders functionality in the UI. Model folders provide "
                "a dedicated space for storing and managing ML model artifacts. Disable if "
                "not using model management features."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="true"),
        ),
    ]


class APIConfig(BaseConfigSchema):
    """Configuration for Backend.AI Manager API connection.

    Specifies how the web server connects to the Backend.AI Manager API server.
    """

    domain: Annotated[
        str,
        Field(default="default"),
        BackendAIConfigMeta(
            description=(
                "Backend.AI domain name for API requests. Domains provide logical separation "
                "of users and resources. Use 'default' for single-domain deployments or "
                "specify the domain name for multi-tenant setups."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="default", prod="default"),
        ),
    ]
    endpoint: Annotated[
        CommaSeparatedStrList,
        Field(
            default_factory=lambda: CommaSeparatedStrList("http://127.0.0.1:8080"),
            min_length=1,
        ),
        BackendAIConfigMeta(
            description=(
                "Backend.AI Manager API endpoint URL(s). Multiple endpoints can be specified "
                "as comma-separated values for load balancing and high availability. "
                "The web server will distribute requests across all endpoints."
            ),
            added_version="25.12.0",
            example=ConfigExample(
                local="http://127.0.0.1:8080",
                prod="http://manager-api:8080,http://manager-api-2:8080",
            ),
        ),
    ]
    text: Annotated[
        str,
        Field(default="Backend.AI API"),
        BackendAIConfigMeta(
            description=(
                "Display text for the API endpoint shown in the web UI. This label appears "
                "in settings and debugging panels. Customize for branded deployments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="Backend.AI API", prod="Production API"),
        ),
    ]
    ssl_verify: Annotated[
        bool,
        Field(
            default=True,
            validation_alias=AliasChoices("ssl_verify", "ssl-verify"),
            serialization_alias="ssl-verify",
        ),
        BackendAIConfigMeta(
            description=(
                "Verify SSL certificates when connecting to the Manager API. Disable only "
                "for development with self-signed certificates. Always enable in production "
                "for security."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    auth_token_name: Annotated[
        str,
        Field(
            default="sToken",
            validation_alias=AliasChoices("auth_token_name", "auth-token-name"),
            serialization_alias="auth-token-name",
        ),
        BackendAIConfigMeta(
            description=(
                "Name of the authentication token cookie/header used for API requests. "
                "Default is 'sToken'. Change only if customizing the authentication flow "
                "or integrating with external identity providers."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="sToken", prod="sToken"),
        ),
    ]
    connection_limit: Annotated[
        int,
        Field(
            default=100,
            ge=1,
            validation_alias=AliasChoices("connection_limit", "connection-limit"),
            serialization_alias="connection-limit",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of simultaneous connections to the Manager API. This limits "
                "concurrent API requests to prevent overloading the manager. Increase for "
                "high-traffic deployments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="50", prod="200"),
        ),
    ]


class RedisHelperConfig(BaseConfigSchema):
    """Helper configuration for Redis connection timeouts.

    Fine-tunes Redis connection behavior for the web server.
    """

    socket_timeout: Annotated[
        float,
        Field(
            default=5.0,
            validation_alias=AliasChoices("socket_timeout", "socket-timeout"),
            serialization_alias="socket_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for Redis socket operations (read/write). If a Redis "
                "operation takes longer than this, it will timeout. Increase for slow "
                "networks or heavily loaded Redis servers."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="5.0", prod="10.0"),
        ),
    ]
    socket_connect_timeout: Annotated[
        float,
        Field(
            default=2.0,
            validation_alias=AliasChoices("socket_connect_timeout", "socket-connect-timeout"),
            serialization_alias="socket_connect_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Timeout in seconds for establishing a connection to Redis. If connection "
                "cannot be established within this time, it will fail. Increase for "
                "remote Redis servers with high latency."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="2.0", prod="5.0"),
        ),
    ]
    reconnect_poll_timeout: Annotated[
        float,
        Field(
            default=0.3,
            validation_alias=AliasChoices("reconnect_poll_timeout", "reconnect-poll-timeout"),
            serialization_alias="reconnect_poll_timeout",
        ),
        BackendAIConfigMeta(
            description=(
                "Polling interval in seconds when attempting to reconnect to Redis after "
                "a connection loss. Lower values provide faster reconnection but increase "
                "CPU usage during outages."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="0.3", prod="0.5"),
        ),
    ]


class WebServerRedisConfig(BaseConfigSchema):
    """Redis database configuration for the web server.

    Specifies which Redis database number to use for web server data.
    """

    db: Annotated[
        int,
        Field(default=0),
        BackendAIConfigMeta(
            description=(
                "Redis database number (0-15) to use for web server data. Different database "
                "numbers provide logical separation of data within the same Redis instance. "
                "Ensure this doesn't conflict with other Backend.AI components."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="0", prod="5"),
        ),
    ]


class SessionConfig(BaseConfigSchema):
    """Configuration for user session management.

    Controls session storage, timeouts, and security features like login rate limiting.
    """

    redis: Annotated[
        RedisConfig,
        Field(default_factory=RedisConfig),
        BackendAIConfigMeta(
            description=(
                "Redis configuration for session storage. Sessions are stored in Redis for "
                "fast access and horizontal scalability. Use a dedicated Redis instance or "
                "database for production."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    max_age: Annotated[
        int,
        Field(
            default=604800,
            validation_alias=AliasChoices("max_age", "max-age"),
            serialization_alias="max-age",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum session age in seconds. Default is 604800 (7 days). After this time, "
                "users must re-authenticate. Shorter values improve security but require "
                "more frequent logins."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="604800", prod="86400"),
        ),
    ]
    login_session_extension_sec: Annotated[
        Optional[int],
        Field(
            default=None,
            validation_alias=AliasChoices(
                "login_session_extension_sec", "login-session-extension-sec"
            ),
            serialization_alias="login-session-extension-sec",
        ),
        BackendAIConfigMeta(
            description=(
                "Seconds to extend the session on each user activity. When set, active users "
                "get their session extended automatically. Leave empty (None) to use fixed "
                "session duration without extension."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="3600"),
        ),
    ]
    flush_on_startup: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("flush_on_startup", "flush-on-startup"),
            serialization_alias="flush-on-startup",
        ),
        BackendAIConfigMeta(
            description=(
                "Clear all existing sessions when the web server starts. Enable during "
                "development or after security incidents. In production, enable only if "
                "you want to force all users to re-login on restart."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]
    login_block_time: Annotated[
        int,
        Field(
            default=1200,
            validation_alias=AliasChoices("login_block_time", "login-block-time"),
            serialization_alias="login-block-time",
        ),
        BackendAIConfigMeta(
            description=(
                "Duration in seconds to block login attempts after exceeding the failure limit. "
                "Default is 1200 (20 minutes). This helps prevent brute-force password attacks."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="60", prod="1200"),
        ),
    ]
    login_allowed_fail_count: Annotated[
        int,
        Field(
            default=10,
            validation_alias=AliasChoices("login_allowed_fail_count", "login-allowed-fail-count"),
            serialization_alias="login-allowed-fail-count",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of failed login attempts before blocking. After this many "
                "failures, the IP or account is blocked for login_block_time seconds. "
                "Lower values are more secure but may frustrate legitimate users."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="10", prod="5"),
        ),
    ]
    auto_logout: Annotated[
        bool,
        Field(
            default=False,
            validation_alias=AliasChoices("auto_logout", "auto-logout"),
            serialization_alias="auto-logout",
        ),
        BackendAIConfigMeta(
            description=(
                "Automatically log out users after a period of inactivity. When enabled, "
                "inactive sessions are terminated. Works with session extension settings "
                "to control idle timeout behavior."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="true"),
        ),
    ]
    max_count_for_preopen_ports: Annotated[
        int,
        Field(
            default=10,
            validation_alias=AliasChoices(
                "max_count_for_preopen_ports", "max-count-for-preopen-ports"
            ),
            serialization_alias="max-count-for-preopen-ports",
        ),
        BackendAIConfigMeta(
            description=(
                "Maximum number of ports that can be pre-opened for a session. Pre-opened ports "
                "are reserved before the session starts for services like Jupyter or SSH. "
                "Higher values allow more services but consume more resources."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="10", prod="5"),
        ),
    ]


class LicenseConfig(BaseConfigSchema):
    """License information for the Backend.AI deployment.

    Displays license metadata in the web UI. For Enterprise editions,
    this shows the license validity period.
    """

    edition: Annotated[
        str,
        Field(default="Open Source"),
        BackendAIConfigMeta(
            description=(
                "Backend.AI edition name. 'Open Source' for community edition, "
                "'Enterprise' for commercial deployments. This is displayed in the "
                "UI footer and about page."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="Open Source", prod="Enterprise"),
        ),
    ]
    valid_since: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("valid_since", "valid-since"),
            serialization_alias="valid-since",
        ),
        BackendAIConfigMeta(
            description=(
                "Start date of the license validity period in YYYY-MM-DD format. "
                "Empty for Open Source edition. Used to display license information "
                "to administrators."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="2024-01-01"),
        ),
    ]
    valid_until: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("valid_until", "valid-until"),
            serialization_alias="valid-until",
        ),
        BackendAIConfigMeta(
            description=(
                "End date of the license validity period in YYYY-MM-DD format. "
                "Empty for Open Source edition. Administrators are notified when "
                "the license is approaching expiration."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="", prod="2025-12-31"),
        ),
    ]


class EventLoopType(enum.StrEnum):
    ASYNCIO = "asyncio"
    UVLOOP = "uvloop"


class WebServerConfig(BaseConfigSchema):
    """Core web server runtime configuration.

    Controls low-level server settings like event loop, IPC paths, and process management.
    """

    event_loop: Annotated[
        EventLoopType,
        Field(
            default=EventLoopType.UVLOOP,
            validation_alias=AliasChoices("event_loop", "event-loop"),
            serialization_alias="event-loop",
        ),
        BackendAIConfigMeta(
            description=(
                "Async event loop implementation. 'uvloop' (default) provides better "
                "performance using libuv. 'asyncio' uses Python's standard library "
                "implementation, which may be more compatible in some environments."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="asyncio", prod="asyncio"),
        ),
    ]
    ipc_base_path: Annotated[
        AutoDirectoryPath,
        Field(
            default=AutoDirectoryPath("/tmp/backend.ai/ipc"),
            validation_alias=AliasChoices("ipc_base_path", "ipc-base-path"),
            serialization_alias="ipc-base-path",
        ),
        BackendAIConfigMeta(
            description=(
                "Base directory for Unix domain sockets used for inter-process communication. "
                "The directory is created automatically if it doesn't exist. "
                "Must be writable by the web server process."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="/tmp/backend.ai/ipc", prod="/var/run/backend.ai/ipc"),
        ),
    ]
    pid_file: Annotated[
        Path,
        Field(
            default=Path(os.devnull),
            validation_alias=AliasChoices("pid_file", "pid-file"),
            serialization_alias="pid-file",
        ),
        BackendAIConfigMeta(
            description=(
                "Path to write the web server process ID. Used by process managers "
                "and monitoring tools. Set to /dev/null (default) to disable PID file creation."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="/dev/null", prod="/var/run/backend.ai/webserver.pid"),
        ),
    ]


class ApolloRouterConfig(BaseConfigSchema):
    """Configuration for Apollo Router GraphQL gateway.

    Apollo Router provides a federated GraphQL gateway for distributed schema composition.
    """

    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable Apollo Router integration for GraphQL federation. When enabled, "
                "GraphQL requests are routed through Apollo Router instead of directly "
                "to the Manager API. Useful for advanced GraphQL architectures."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="false", prod="false"),
        ),
    ]
    endpoints: Annotated[
        CommaSeparatedStrList,
        Field(
            default_factory=lambda: CommaSeparatedStrList(["http://127.0.0.1:4000"]),
            validation_alias=AliasChoices("endpoint", "endpoints"),
            serialization_alias="endpoints",
        ),
        BackendAIConfigMeta(
            description=(
                "Apollo Router endpoint URL(s). Multiple endpoints can be specified "
                "as comma-separated values for load balancing. Only used when Apollo "
                "Router is enabled."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="http://127.0.0.1:4000", prod="http://apollo-router:4000"),
        ),
    ]


class DebugConfig(BaseConfigSchema):
    """Debug mode configuration for the web server.

    Enables additional logging and debugging features for development.
    """

    enabled: Annotated[
        bool,
        Field(default=False),
        BackendAIConfigMeta(
            description=(
                "Enable debug mode for the web server. When enabled, provides verbose "
                "logging, detailed error messages, and development tools. Never enable "
                "in production as it may expose sensitive information."
            ),
            added_version="25.12.0",
            example=ConfigExample(local="true", prod="false"),
        ),
    ]


class WebServerUnifiedConfig(BaseConfigSchema):
    """Unified configuration for the Backend.AI web server.

    This is the root configuration model that aggregates all web server settings.
    Load this configuration from a TOML file to configure the web server.
    """

    service: Annotated[
        ServiceConfig,
        Field(default_factory=ServiceConfig),
        BackendAIConfigMeta(
            description=(
                "Core service configuration including bind address, SSL settings, "
                "and authentication options."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    security: Annotated[
        SecurityConfig,
        Field(default_factory=SecurityConfig),
        BackendAIConfigMeta(
            description=(
                "Security settings including request/response policies and Content "
                "Security Policy (CSP) configuration."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    resources: Annotated[
        ResourcesConfig,
        Field(default_factory=ResourcesConfig),
        BackendAIConfigMeta(
            description=(
                "Resource limits for the UI including maximum CPU, memory, and "
                "accelerator allocations per container."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    environments: Annotated[
        EnvironmentsConfig,
        Field(default_factory=EnvironmentsConfig),
        BackendAIConfigMeta(
            description=(
                "Container image environment settings including allowlist and display preferences."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    plugin: Annotated[
        PluginConfig,
        Field(default_factory=PluginConfig),
        BackendAIConfigMeta(
            description="Web UI plugin configuration for extending the interface.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    pipeline: Annotated[
        PipelineConfig,
        Field(default_factory=PipelineConfig),
        BackendAIConfigMeta(
            description=(
                "Backend.AI Pipeline service integration settings for ML workflow automation."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    ui: Annotated[
        UIConfig,
        Field(default_factory=UIConfig),
        BackendAIConfigMeta(
            description="UI customization settings including default environments and menu visibility.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    api: Annotated[
        APIConfig,
        Field(default_factory=APIConfig),
        BackendAIConfigMeta(
            description=(
                "Backend.AI Manager API connection settings including endpoints and "
                "connection limits."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    jwt: Annotated[
        SharedJWTConfig,
        Field(default_factory=SharedJWTConfig),
        BackendAIConfigMeta(
            description=(
                "JWT authentication configuration shared between Manager and Web Server "
                "for stateless token-based authentication."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    session: Annotated[
        SessionConfig,
        Field(default_factory=SessionConfig),
        BackendAIConfigMeta(
            description=(
                "User session management settings including Redis storage, timeouts, "
                "and login security."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    license: Annotated[
        LicenseConfig,
        Field(default_factory=LicenseConfig),
        BackendAIConfigMeta(
            description="License information displayed in the web interface.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    webserver: Annotated[
        WebServerConfig,
        Field(default_factory=WebServerConfig),
        BackendAIConfigMeta(
            description=(
                "Core web server runtime settings including event loop and process management."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    otel: Annotated[
        OTELConfig,
        Field(default_factory=OTELConfig),  # type: ignore[arg-type]
        BackendAIConfigMeta(
            description="OpenTelemetry integration for distributed tracing and metrics collection.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    etcd: Annotated[
        EtcdConfig,
        Field(default_factory=EtcdConfig),  # type: ignore[arg-type]
        BackendAIConfigMeta(
            description=(
                "etcd connection settings for distributed configuration and "
                "coordination with other Backend.AI components."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    pyroscope: Annotated[
        PyroscopeConfig,
        Field(default_factory=PyroscopeConfig),  # type: ignore[arg-type]
        BackendAIConfigMeta(
            description="Pyroscope continuous profiling integration for performance analysis.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    service_discovery: Annotated[
        ServiceDiscoveryConfig,
        Field(
            default_factory=ServiceDiscoveryConfig,  # type: ignore[arg-type]
            validation_alias=AliasChoices("service-discovery", "service_discovery"),
            serialization_alias="service-discovery",
        ),
        BackendAIConfigMeta(
            description=(
                "Service discovery configuration for automatic detection and "
                "connection to Backend.AI services."
            ),
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    apollo_router: Annotated[
        ApolloRouterConfig,
        Field(
            default_factory=ApolloRouterConfig,
            validation_alias=AliasChoices("apollo_router", "apollo-router"),
            serialization_alias="apollo-router",
        ),
        BackendAIConfigMeta(
            description="Apollo Router GraphQL gateway configuration for federated schemas.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    logging: Annotated[
        LoggingConfig,
        Field(default_factory=LoggingConfig),
        BackendAIConfigMeta(
            description="Logging configuration for log levels, formats, and destinations.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]
    debug: Annotated[
        DebugConfig,
        Field(default_factory=DebugConfig),
        BackendAIConfigMeta(
            description="Debug mode settings for development and troubleshooting.",
            added_version="25.12.0",
            composite=CompositeType.FIELD,
        ),
    ]

    # TODO: Remove me after changing config injection logic
    model_config = ConfigDict(
        extra="allow",
    )
