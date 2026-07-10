from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from . import __version__
from .types import Accelerator, CliArgs, EndpointProtocol, FrontendMode, InstallModes


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "--mode",
    type=click.Choice([*InstallModes.__members__], case_sensitive=False),
    default=None,
    help="Override the installation mode. [default: auto-detect]",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Run the installer non-interactively from the given CLI options.",
)
@click.option(
    "--target-path",
    type=str,
    default=str(Path.home() / "backendai"),
    help="Explicitly set the target installation path. [default: ~/backendai]",
)
@click.option(
    "--show-guide",
    is_flag=True,
    default=False,
    help="Show the post-install guide using INSTALL-INFO if present.",
)
@click.option(
    "--accelerator",
    type=click.Choice([a.value for a in Accelerator], case_sensitive=False),
    default=None,
    show_default=True,
    help="Select accelerator plugin (cuda, cuda_mock, cuda_mig_mock, rocm_mock, none)",
)
@click.option(
    "--headless",
    is_flag=True,
    default=False,
    help="Run the installer as headless mode.",
)
@click.option(
    "--public-facing-address",
    type=str,
    default="127.0.0.1",
    help="Set public facing address for the Backend.AI server.",
)
@click.option(
    "--fqdn-prefix",
    type=str,
    default=None,
    help="FQDN prefix for generating domain names (e.g., '786cdf' generates 786cdf.app.backend.ai, 786cdf.apphub.backend.ai, etc.).",
)
@click.option(
    "--tls-advertised",
    is_flag=True,
    default=False,
    help="Advertise TLS endpoints to external clients.",
)
@click.option(
    "--advertised-port",
    type=int,
    default=443,
    help="Advertised port for public endpoints (default: 443).",
)
@click.option(
    "--endpoint-protocol",
    type=click.Choice([p.value for p in EndpointProtocol], case_sensitive=False),
    default=None,
    help="Force endpoint protocol in webserver (http or https). If not set, auto-detected.",
)
@click.option(
    "--frontend-mode",
    type=click.Choice([m.value for m in FrontendMode], case_sensitive=False),
    default=FrontendMode.PORT.value,
    help=(
        "App-proxy frontend mode: 'port' (default), 'wildcard', or 'traefik' "
        "(delegates the dataplane to a Traefik container in the halfstack)."
    ),
)
@click.option(
    "--use-wildcard-binding",
    is_flag=True,
    default=False,
    help="Use wildcard domain binding for app-proxy worker.",
)
@click.option(
    "--otel-endpoint",
    type=str,
    default=None,
    help="OpenTelemetry collector endpoint (e.g., http://10.122.10.56:4317).",
)
@click.option(
    "--metric-access-cidr",
    type=str,
    default="0.0.0.0/0",
    help="CIDR for metric access allowed hosts (default: 0.0.0.0/0).",
)
@click.option(
    "--with-harbor",
    is_flag=True,
    default=False,
    help="Also install a local Harbor container registry (dev mode only).",
)
@click.option(
    "--harbor-hostname",
    type=str,
    default=None,
    help=(
        "Hostname for the local Harbor instance "
        "(must be a non-loopback address; defaults to host.docker.internal "
        "when --public-facing-address is a loopback)."
    ),
)
@click.option(
    "--harbor-http-port",
    type=int,
    default=8084,
    show_default=True,
    help="HTTP port for the local Harbor instance.",
)
@click.option(
    "--harbor-admin-password",
    type=str,
    default="Harbor12345",
    show_default=False,
    help=(
        "Initial admin password for the local Harbor instance. WARNING: "
        "if omitted, a well-known default value is used — override it for "
        "anything beyond a throwaway dev box."
    ),
)
@click.option(
    "--harbor-download-uri",
    type=str,
    default=(
        "https://github.com/goharbor/harbor/releases/download/"
        "v2.11.0/harbor-offline-installer-v2.11.0.tgz"
    ),
    show_default=False,
    help="Harbor offline installer archive URL to download.",
)
@click.option(
    "--harbor-download-sha256",
    type=str,
    default=None,
    help=(
        "Expected SHA-256 of the downloaded Harbor archive. When set, the "
        "installer verifies the downloaded file against this digest and "
        "aborts on mismatch. When unset, no integrity check is performed."
    ),
)
@click.option(
    "--with-sftp-agent",
    is_flag=True,
    default=False,
    help=(
        "Also configure a dedicated SFTP agent (multi-agent per node). "
        "Creates agent-sftp.toml with distinct ports and the 'upload' "
        "scaling group; start it with './dev start sftp-agent'."
    ),
)
@click.option(
    "--enable-observability",
    is_flag=True,
    default=False,
    help=(
        "Bring up the halfstack 'observability' Compose profile (Prometheus,"
        " Grafana, OTel collector, Loki, Tempo, Pyroscope, exporters) and enable"
        " Pyroscope / OTel in component configs."
    ),
)
@click.option(
    "--enable-storage",
    is_flag=True,
    default=False,
    help="Bring up the halfstack 'storage' Compose profile (MinIO).",
)
@click.option(
    "--enable-telemetry",
    "enable_telemetry",
    flag_value="on",
    default=None,
    help=(
        "Bring up the halfstack 'telemetry' Compose profile (OTel collector"
        " + Loki) and enable [otel] in component configs. Default ON in"
        " DEVELOP install mode, OFF in PACKAGE install mode."
    ),
)
@click.option(
    "--disable-telemetry",
    "enable_telemetry",
    flag_value="off",
    help="Force the 'telemetry' profile OFF (overrides DEVELOP mode default).",
)
@click.version_option(version=__version__)
@click.pass_context
def main(
    _cli_ctx: click.Context,
    mode: InstallModes | None,
    target_path: str,
    show_guide: bool,
    non_interactive: bool,
    headless: bool,
    public_facing_address: str,
    fqdn_prefix: str | None,
    tls_advertised: bool,
    advertised_port: int,
    endpoint_protocol: str | None,
    frontend_mode: str,
    use_wildcard_binding: bool,
    otel_endpoint: str | None,
    metric_access_cidr: str,
    with_harbor: bool,
    harbor_hostname: str | None,
    harbor_http_port: int,
    harbor_admin_password: str,
    harbor_download_uri: str,
    harbor_download_sha256: str | None,
    with_sftp_agent: bool,
    enable_observability: bool,
    enable_storage: bool,
    enable_telemetry: str | None,
    accelerator: str,
) -> None:
    """The installer"""
    from rich.console import Console

    from .app import InstallerApp

    # check sudo permission
    console = Console(stderr=True)
    if os.geteuid() == 0:
        console.print(
            "[bright_red] The script should not be run as root, while it requires"
            " the passwordless sudo privilege."
        )
        sys.exit(1)
    # start installer
    args = CliArgs(
        mode=mode,
        target_path=target_path,
        show_guide=show_guide,
        non_interactive=non_interactive,
        public_facing_address=public_facing_address,
        accelerator=accelerator,
        fqdn_prefix=fqdn_prefix,
        tls_advertised=tls_advertised,
        advertised_port=advertised_port,
        endpoint_protocol=EndpointProtocol(endpoint_protocol) if endpoint_protocol else None,
        frontend_mode=FrontendMode(frontend_mode),
        use_wildcard_binding=use_wildcard_binding,
        otel_endpoint=otel_endpoint,
        metric_access_cidr=metric_access_cidr,
        with_harbor=with_harbor,
        harbor_hostname=harbor_hostname,
        harbor_http_port=harbor_http_port,
        harbor_admin_password=harbor_admin_password,
        harbor_download_uri=harbor_download_uri,
        harbor_download_sha256=harbor_download_sha256,
        with_sftp_agent=with_sftp_agent,
        enable_observability=enable_observability,
        enable_storage=enable_storage,
        enable_telemetry=(None if enable_telemetry is None else (enable_telemetry == "on")),
    )
    app = InstallerApp(args)
    app.run(headless=headless)
